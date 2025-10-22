"""
Модуль для управления работой с VM
"""
import os
import shutil
from datetime import datetime
from vm_scanner import vm_scanner
from logger import logger


class VMManager:
    """Менеджер для работы с виртуальными машинами"""
    
    def __init__(self):
        self.manual_ip_part = None
        self.vm_address = None
    
    def set_ip_part(self, ip_part):
        """Устанавливает IP часть для VM"""
        self.manual_ip_part = ip_part
        self.vm_address = self._get_vm_path()
        logger.info(f"IP установлен: {ip_part}")
    
    def _get_vm_path(self):
        """Генерирует путь к VM с автоматическим определением порта"""
        if self.manual_ip_part is None:
            return None
        
        try:
            # Используем сканер VM для автоматического определения порта
            vm_path = vm_scanner.get_vm_path(self.manual_ip_part)
            if vm_path:
                logger.info(f"Путь к VM определен: {vm_path}")
                return vm_path
            else:
                logger.error(f"Не удалось определить путь к VM для IP {self.manual_ip_part}")
                return None
        except Exception as e:
            logger.error(f"Ошибка определения пути к VM: {e}")
            return None
    
    def find_latest_excel_file(self, screenshots_folder):
        """Находит самый новый Excel файл в папке скриншотов"""
        try:
            excel_files = []
            for filename in os.listdir(screenshots_folder):
                if filename.lower().endswith('.xlsx'):
                    file_path = os.path.join(screenshots_folder, filename)
                    excel_files.append(file_path)

            # Сортируем по дате создания (новые первыми)
            excel_files.sort(key=os.path.getctime, reverse=True)
            return excel_files[0] if excel_files else None

        except Exception as e:
            logger.error(f"Ошибка поиска Excel файлов: {e}")
            return None
    
    def send_excel_to_vm(self, excel_file_path, vm_path=None):
        """Отправляет Excel файл на VM по указанному пути"""
        try:
            if not os.path.exists(excel_file_path):
                return False, "Excel файл не найден"

            # Создаем имя для копии на VM
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_name = os.path.basename(excel_file_path)
            vm_filename = f"{original_name[:-5]}_vm_{timestamp}.xlsx"

            # Копируем на VM
            success = self._copy_to_vm(excel_file_path, vm_filename, vm_path)

            if success:
                return True, f"Excel успешно отправлен на VM: {vm_filename}"
            else:
                return False, "Не удалось отправить файл на VM"

        except Exception as e:
            logger.error(f"Ошибка отправки: {str(e)}")
            return False, f"Ошибка отправки: {str(e)}"
    
    def _copy_to_vm(self, local_file_path, filename, vm_path=None):
        """Копирует файл на VM"""
        try:
            # Используем переданный путь или self.vm_address
            target_path = vm_path if vm_path is not None else self.vm_address

            if target_path is None:
                logger.error("Путь к VM не определен")
                return False

            logger.info(f"Копируем в: {target_path}")

            # Создаем директорию на VM если не существует
            os.makedirs(target_path, exist_ok=True)

            # Путь назначения на VM
            vm_file_path = os.path.join(target_path, filename)
            logger.info(f"Полный путь файла: {vm_file_path}")

            # Копируем файл
            shutil.copy2(local_file_path, vm_file_path)
            logger.info("Файл скопирован")

            # Проверяем что файл скопировался
            if os.path.exists(vm_file_path):
                file_size = os.path.getsize(vm_file_path)
                logger.info(f"Файл создан, размер: {file_size} байт")
                return True
            else:
                logger.error("Файл не создался после копирования")
                return False

        except Exception as e:
            logger.error(f"Ошибка копирования на VM: {e}")
            return False
    
    def copy_file_to_vm(self, local_file_path, vm_path):
        """Копирует файл на VM с проверкой результата"""
        try:
            excel_filename = os.path.basename(local_file_path)
            remote_file_path = os.path.join(vm_path, excel_filename)

            logger.info(f"Копируем файл: {local_file_path} -> {remote_file_path}")

            # Пробуем скопировать файл
            shutil.copy2(local_file_path, remote_file_path)

            # Проверяем что файл скопировался
            if os.path.exists(remote_file_path):
                success = True
                message = f"Excel успешно отправлен на VM: {excel_filename}"
                logger.info(f"Файл успешно скопирован на VM: {excel_filename}")
            else:
                success = False
                message = "Файл не был скопирован на VM"
                logger.error("Файл не был скопирован на VM")

            return success, message

        except Exception as e:
            error_msg = f"Ошибка копирования: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
