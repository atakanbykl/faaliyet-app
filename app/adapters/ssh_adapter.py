"""
FieldOps Assistant - Uzak SSH Çalıştırma Adaptörü (SSHExecutionAdapter)
Windows destek bilgisayarından hedef Linux cihaza SSH ve SFTP üzerinden
bağlanarak komut yürütme, konfigürasyon basma ve 20-30GB log çekme işlemlerini yönetir.
"""

from __future__ import annotations
import os
import posixpath
from pathlib import Path
from typing import Callable, Optional, Tuple
import paramiko

from app.adapters.base_adapter import BaseExecutionAdapter, CommandResult
from app.core.models import TargetDeviceConfig


class SSHExecutionAdapter(BaseExecutionAdapter):
    """Paramiko tabanlı uzaktan SSH/SFTP yönetim adaptörü."""

    def __init__(self, config: TargetDeviceConfig):
        self.config = config
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None

    def _get_client(self) -> paramiko.SSHClient:
        """SSH istemcisini hazırlar veya mevcut bağlantıyı döner."""
        if self._client and self._client.get_transport() and self._client.get_transport().is_active():
            return self._client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.config.host,
            "port": self.config.port,
            "username": self.config.username,
            "timeout": 10,
        }
        if self.config.password:
            connect_kwargs["password"] = self.config.password
        if self.config.key_path and os.path.exists(self.config.key_path):
            connect_kwargs["key_filename"] = self.config.key_path

        client.connect(**connect_kwargs)
        self._client = client
        return client

    def _get_sftp(self) -> paramiko.SFTPClient:
        """SFTP istemcisini başlatır."""
        if self._sftp:
            try:
                self._sftp.stat(".")
                return self._sftp
            except Exception:
                pass
        client = self._get_client()
        self._sftp = client.open_sftp()
        return self._sftp

    def close(self) -> None:
        """Bağlantıları güvenle sonlandırır."""
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def test_connection(self) -> Tuple[bool, str]:
        """Uzak SSH bağlantısını test eder."""
        try:
            client = self._get_client()
            stdin, stdout, stderr = client.exec_command("echo 'FieldOps_Connection_OK'", timeout=5)
            out = stdout.read().decode("utf-8").strip()
            if "FieldOps_Connection_OK" in out:
                return True, f"SSH bağlantısı başarılı: {self.config.username}@{self.config.host}:{self.config.port}"
            return False, f"Beklenmeyen yanıt: {out}"
        except Exception as e:
            return False, f"SSH bağlantı hatası: {e}"

    def execute_command(self, command: str) -> CommandResult:
        """Uzak cihazda kabuk komutu çalıştırır."""
        try:
            client = self._get_client()
            stdin, stdout, stderr = client.exec_command(command, timeout=300)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode("utf-8", errors="replace")
            err_str = stderr.read().decode("utf-8", errors="replace")
            return CommandResult(
                success=(exit_code == 0),
                exit_code=exit_code,
                stdout=out_str,
                stderr=err_str
            )
        except Exception as e:
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e)
            )

    def get_installed_version(self, version_command: str) -> Optional[str]:
        """Uzakta kurulu yazılımın versiyonunu sorgular."""
        res = self.execute_command(version_command)
        if res.success and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
        return None

    def deploy_package(
        self,
        local_package_path: str,
        target_install_path: str,
        service_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """Paketi SFTP ile uzaktaki cihaza yükler ve tar ile açar."""
        try:
            sftp = self._get_sftp()
            local_pkg = Path(local_package_path)
            if not local_pkg.exists():
                return False, f"Yerel paket bulunamadı: {local_package_path}"

            remote_tmp_pkg = f"/tmp/{local_pkg.name}"
            # SFTP ile yükle
            sftp.put(str(local_pkg), remote_tmp_pkg, callback=progress_callback)

            # Servisi durdur
            if service_name:
                self.execute_command(f"systemctl stop {service_name}")

            # Hedef klasörü oluştur ve arşivi aç
            self.execute_command(f"mkdir -p {target_install_path}")
            if local_pkg.name.endswith(".tar.gz") or local_pkg.name.endswith(".tgz"):
                unpack_res = self.execute_command(f"tar -xzf {remote_tmp_pkg} -C {target_install_path}")
                if not unpack_res.success:
                    return False, f"Uzak arşiv açma hatası: {unpack_res.stderr}"
            else:
                self.execute_command(f"cp {remote_tmp_pkg} {target_install_path}/")

            # Geçici paketi temizle
            self.execute_command(f"rm -f {remote_tmp_pkg}")

            # Servisi yeniden başlat
            if service_name:
                self.execute_command(f"systemctl start {service_name}")

            return True, f"Paket başarıyla yüklendi: {target_install_path}"
        except Exception as e:
            return False, f"Dağıtım hatası: {e}"

    def apply_configuration(self, config_content: str, remote_config_path: str) -> Tuple[bool, str]:
        """Konfigürasyonu SFTP üzerinden hedef dosyaya aktarır."""
        try:
            sftp = self._get_sftp()
            # Hedef klasörün varlığını sağla
            remote_dir = posixpath.dirname(remote_config_path)
            self.execute_command(f"mkdir -p {remote_dir}")

            with sftp.open(remote_config_path, "w") as f:
                f.write(config_content)
            return True, f"Uzak konfigürasyon güncellendi: {remote_config_path}"
        except Exception as e:
            return False, f"Konfigürasyon aktarım hatası: {e}"

    def pull_active_configuration(self, remote_config_path: str) -> Tuple[bool, str]:
        """Uzak cihazdaki aktif konfigürasyon dosyasını SFTP ile okur."""
        try:
            sftp = self._get_sftp()
            with sftp.open(remote_config_path, "r") as f:
                content = f.read().decode("utf-8")
            return True, content
        except Exception as e:
            return False, f"Konfigürasyon çekme hatası: {e}"

    def get_free_disk_space_gb(self, target_path: str) -> float:
        """Uzak cihazda 'df -k' ile boş alanı sorgular."""
        res = self.execute_command(f"df -k {target_path} | tail -1 | awk '{{print $4}}'")
        if res.success and res.stdout.strip():
            try:
                free_kb = int(res.stdout.strip())
                return free_kb / (1024 * 1024)
            except Exception:
                pass
        return 0.0

    def compress_logs(
        self,
        log_source_dir: str,
        output_archive_path: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Uzak cihazda çok çekirdekli veya standart tar ile sıkıştırma tetikler.
        Bitişinde SHA-256 çıktısını döner.
        """
        if log_callback:
            log_callback(f"Uzak cihazda sıkıştırma başlatılıyor ({log_source_dir})...")

        # Uzak hedef klasörü aç
        out_dir = posixpath.dirname(output_archive_path)
        self.execute_command(f"mkdir -p {out_dir}")

        # Pigz kontrolü
        check_pigz = self.execute_command("which pigz")
        has_pigz = check_pigz.success and bool(check_pigz.stdout.strip())

        parent_dir = posixpath.dirname(log_source_dir)
        base_name = posixpath.basename(log_source_dir)

        if has_pigz:
            cmd = f"tar -I pigz -cf {output_archive_path} -C {parent_dir} {base_name}"
        else:
            cmd = f"tar -czf {output_archive_path} -C {parent_dir} {base_name}"

        res = self.execute_command(cmd)
        if not res.success:
            return False, f"Uzak sıkıştırma hatası: {res.stderr}"

        # Uzakta SHA-256 hesapla
        sha_res = self.execute_command(f"sha256sum {output_archive_path} | awk '{{print $1}}'")
        sha_hash = sha_res.stdout.strip() if sha_res.success else "Bilinmiyor"

        if log_callback:
            log_callback(f"Uzak sıkıştırma tamamlandı. SHA-256: {sha_hash}")

        return True, sha_hash

    def fetch_archive(
        self,
        source_archive_path: str,
        local_destination_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """SFTP üzerinden 20-30 GB arşivi yerel ortama veya USB'ye indirir."""
        try:
            sftp = self._get_sftp()
            local_dest = Path(local_destination_path)
            local_dest.parent.mkdir(parents=True, exist_ok=True)

            sftp.get(source_archive_path, str(local_dest), callback=progress_callback)
            return True, f"Arşiv başarıyla indirildi: {local_destination_path}"
        except Exception as e:
            return False, f"İndirme hatası: {e}"

