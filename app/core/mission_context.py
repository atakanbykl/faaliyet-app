"""
FieldOps Assistant - Görev Oturumu ve Raporlama Yöneticisi
Saha faaliyetinin durumunu (adım aşamaları, toplanan veriler, kontrol sonuçları)
yönetir, kalıcı görev özeti üretir ve geçmiş oturumları geri yükler.
"""

from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.core.app_paths import AppPaths
from app.core.models import MissionSession


class MissionManager:
    """Görev oturumlarını oluşturur, günceller, diskte arşivler ve geçmiş oturumları listeler."""

    def __init__(self, missions_dir: Optional[Path] = None):
        self.missions_dir = missions_dir or AppPaths.get_missions_dir()
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[MissionSession] = None
        self.current_session_dir: Optional[Path] = None

    def list_saved_sessions(self) -> List[MissionSession]:
        """
        Kayıtlı tüm geçmiş faaliyetleri tarar ve en yeniden en eskiye sıralayarak döner.
        """
        sessions: List[MissionSession] = []
        for summary_file in self.missions_dir.glob("*/mission_summary.json"):
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session = MissionSession.from_dict(data)
                    sessions.append(session)
            except Exception:
                continue

        # Tarihe göre tersten sırala (en yeni en üstte)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def load_session(self, session_id: str) -> Optional[MissionSession]:
        """Kayıtlı bir oturumu diskten yükler ve aktif oturum yapar."""
        session_dir = self.missions_dir / session_id
        summary_file = session_dir / "mission_summary.json"

        if not summary_file.exists():
            return None

        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                session = MissionSession.from_dict(data)
                self.current_session = session
                self.current_session_dir = session_dir
                return session
        except Exception:
            return None

    def start_new_session(self, location_id: str, operator_name: str) -> MissionSession:
        """Yeni bir saha faaliyeti oturumu başlatır."""
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"gorev_{now_str}_{location_id}"
        session_dir = self.missions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        session = MissionSession(
            session_id=session_id,
            location_id=location_id,
            operator_name=operator_name or "Saha_Operatoru",
            current_stage=1
        )
        self.current_session = session
        self.current_session_dir = session_dir
        self.save_current_session()
        return session

    def set_current_stage(self, stage: int) -> None:
        """Kaldığı aşamayı günceller ve kaydeder."""
        if self.current_session:
            self.current_session.current_stage = stage
            if stage == 2:
                self.current_session.stage1_completed = True
            elif stage == 3:
                self.current_session.stage2_completed = True
            self.save_current_session()

    def save_current_session(self) -> Optional[Path]:
        """Aktif oturum durumunu JSON olarak kaydeder."""
        if not self.current_session or not self.current_session_dir:
            return None

        summary_file = self.current_session_dir / "mission_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
        return summary_file

    def record_note(self, text: str) -> None:
        """Oturum günlüğüne bir not ekler."""
        if self.current_session:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.current_session.notes.append(f"[{timestamp}] {text}")
            self.save_current_session()

    def store_captured_config(self, config_text: str) -> Path:
        """Sahadan çekilen konfigürasyonu görev arşivine kaydeder."""
        if not self.current_session_dir:
            raise RuntimeError("Aktif görev oturumu bulunamadı!")

        target_file = self.current_session_dir / "retrieved_config.json"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(config_text)

        if self.current_session:
            self.current_session.captured_config_path = str(target_file)
            self.save_current_session()

        return target_file

    def delete_session(self, session_id: str) -> bool:
        """Oturum klasörünü siler."""
        session_dir = self.missions_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                self.current_session_dir = None
            return True
        return False
