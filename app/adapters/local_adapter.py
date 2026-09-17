"""
FieldOps Assistant - Yerel Çalıştırma Adaptörü (LocalExecutionAdapter)
Uygulama doğrudan ana Linux sistemi üzerinde (veya yerel testlerde) çalıştırıldığında
en yüksek I/O performansı için yerel sistem komutlarını ve dosya işlemlerini yürütür.
"""

from __future__ import annotations
import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional, Tuple

from app.adapters.base_adapter import BaseExecutionAdapter, CommandResult


class LocalExecutionAdapter(BaseExecutionAdapter):
    """Doğrudan yerel işletim sistemi üzerinde çalışan adaptör."""

    def test_connection(self) -> Tuple[bool, str]:
        """Yerel sistem her zaman erişilebilirdir."""
        return True, "Yerel sistem erişilebilir (Doğrudan Yerel Mod)."

    def execute_command(self, command: str) -> CommandResult:
        """Yerel kabuk üzerinden komut çalıştırır."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            return CommandResult(
                success=(res.returncode == 0),
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr
            )
        except Exception as e:
            return CommandResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e)
            )

    def get_installed_version(self, version_command: str) -> Optional[str]:
        """Yerel yazılımın versiyonunu sorgular."""
        res = self.execute_command(version_command)
        if res.success and res.stdout.strip():
            # İlk satırdaki sürüm çıktısını al
            return res.stdout.strip().splitlines()[0]
        return None

    def deploy_package(
        self,
        local_package_path: str,
        target_install_path: str,
        service_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """Paketi yerel hedef dizine açar ve servisi yeniden başlatır."""
        pkg = Path(local_package_path)
        dest = Path(target_install_path)
        dest.mkdir(parents=True, exist_ok=True)

        if not pkg.exists():
            return False, f"Paket dosyası bulunamadı: {local_package_path}"

        # Servisi durdur (varsa ve Linux ise)
        if service_name and os.name != "nt":
            self.execute_command(f"systemctl stop {service_name}")

        # Arşivi aç (tar.gz ise)
        if pkg.name.endswith(".tar.gz") or pkg.name.endswith(".tgz"):
            extract_cmd = f"tar -xzf \"{pkg}\" -C \"{dest}\""
            res = self.execute_command(extract_cmd)
            if not res.success:
                return False, f"Arşiv açma hatası: {res.stderr}"
        else:
            # Düz dosya ise kopyala
            shutil.copy2(pkg, dest / pkg.name)

        # Servisi başlat
        if service_name and os.name != "nt":
            self.execute_command(f"systemctl start {service_name}")

        return True, f"Paket başarıyla yüklendi: {target_install_path}"

    def apply_configuration(self, config_content: str, remote_config_path: str) -> Tuple[bool, str]:
        """Konfigürasyonu yerel hedef dosyaya yazar."""
        try:
            target = Path(remote_config_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(config_content)
            return True, f"Konfigürasyon kaydedildi: {target}"
        except Exception as e:
            return False, f"Konfigürasyon yazma hatası: {e}"

    def pull_active_configuration(self, remote_config_path: str) -> Tuple[bool, str]:
        """Yerel konfigürasyon dosyasını okur."""
        target = Path(remote_config_path)
        if not target.exists():
            return False, f"Hedef konfigürasyon dosyası bulunamadı: {target}"
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"Konfigürasyon okuma hatası: {e}"

    def get_free_disk_space_gb(self, target_path: str) -> float:
        """Diskteki boş alanı hesaplar."""
        try:
            check_path = target_path if os.path.exists(target_path) else os.path.dirname(target_path) or "."
            usage = shutil.disk_usage(check_path)
            return usage.free / (1024 ** 3)
        except Exception:
            return 0.0

    def compress_logs(
        self,
        log_source_dir: str,
        output_archive_path: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Log klasörünü tar ile sıkıştırır.
        Sistemde pigz varsa çok çekirdekli, yoksa standart gzip kullanılır.
        """
        src = Path(log_source_dir)
        dest = Path(output_archive_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not src.exists():
            return False, f"Log kaynak klasörü bulunamadı: {log_source_dir}"

        if log_callback:
            log_callback(f"Log sıkıştırma başlatılıyor: {src} -> {dest}")

        # Windows veya Linux tar komutu
        # Linux'ta pigz varsa çok çekirdekli sıkıştırma
        use_pigz = (shutil.which("pigz") is not None) and (os.name != "nt")

        if use_pigz:
            cmd = f"tar -I pigz -cf \"{dest}\" -C \"{src.parent}\" \"{src.name}\""
        else:
            cmd = f"tar -czf \"{dest}\" -C \"{src.parent}\" \"{src.name}\""

        res = self.execute_command(cmd)
        if not res.success:
            # Fallback: Python tarfile modülü
            try:
                import tarfile
                with tarfile.open(dest, "w:gz") as tar:
                    tar.add(src, arcname=src.name)
            except Exception as e:
                return False, f"Sıkıştırma hatası: {e}"

        # SHA-256 hash hesapla
        sha = self.calculate_sha256(dest)
        if log_callback:
            log_callback(f"Sıkıştırma tamamlandı. SHA-256: {sha}")

        return True, sha

    def fetch_archive(
        self,
        source_archive_path: str,
        local_destination_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """Yerel modda dosya kopyalama."""
        src = Path(source_archive_path)
        dest = Path(local_destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not src.exists():
            return False, f"Kaynak arşiv bulunamadı: {src}"

        try:
            total_size = src.stat().st_size
            copied = 0
            chunk_size = 16 * 1024 * 1024  # 16 MB bloklar

            with open(src, "rb") as fsrc, open(dest, "wb") as fdest:
                while True:
                    buf = fsrc.read(chunk_size)
                    if not buf:
                        break
                    fdest.write(buf)
                    copied += len(buf)
                    if progress_callback:
                        progress_callback(copied, total_size)

            return True, f"Arşiv başarıyla kopyalandı: {dest}"
        except Exception as e:
            return False, f"Kopyalama hatası: {e}"

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Büyük dosyalar için bellek tasarruflu blok blok SHA256 hesaplar."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(16 * 1024 * 1024):
                h.update(chunk)
        return h.hexdigest()

