"""
FieldOps Assistant - Temel Çalıştırma Adaptörü Arayüzü (Base Execution Adapter)
Tüm saha komutları, konfigürasyon enjeksiyonu ve büyük log çekme işlemlerinin
ortak soyutlama katmanı.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


@dataclass
class CommandResult:
    """Yürütülen sistem komutunun çıktısı."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str


class BaseExecutionAdapter(ABC):
    """Local ve SSH adaptörlerinin miras aldığı temel sınıf."""

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Hedef sistemle bağlantıyı test eder (True, mesaj) veya (False, hata mesajı)."""
        pass

    @abstractmethod
    def execute_command(self, command: str) -> CommandResult:
        """Sistem komutu çalıştırır."""
        pass

    @abstractmethod
    def get_installed_version(self, version_command: str) -> Optional[str]:
        """Hedef yazılımın kurulu versiyonunu sorgular."""
        pass

    @abstractmethod
    def deploy_package(
        self,
        local_package_path: str,
        target_install_path: str,
        service_name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """Yazılım paketini hedefe aktarır, açar ve servisi yeniden başlatır."""
        pass

    @abstractmethod
    def apply_configuration(self, config_content: str, remote_config_path: str) -> Tuple[bool, str]:
        """Lokasyon konfigürasyonunu hedef dosya yoluna yazar."""
        pass

    @abstractmethod
    def pull_active_configuration(self, remote_config_path: str) -> Tuple[bool, str]:
        """Hedefte çalışan aktif konfigürasyon dosyasının içeriğini okur."""
        pass

    @abstractmethod
    def get_free_disk_space_gb(self, target_path: str) -> float:
        """Hedef sistemdeki boş disk alanını GB cinsinden sorgular."""
        pass

    @abstractmethod
    def compress_logs(
        self,
        log_source_dir: str,
        output_archive_path: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        Cihazda log klasörünü 'tar -czf' (veya varsa pigz ile çok çekirdekli) sıkıştırır.
        """
        pass

    @abstractmethod
    def fetch_archive(
        self,
        source_archive_path: str,
        local_destination_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, str]:
        """Sıkıştırılan 20-30GB arşivi yerel ortama (veya USB'ye) aktarır."""
        pass

