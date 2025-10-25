import os
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG
from PIL import ImageGrab, Image
import keyboard
import win32gui
from config import config
from logger import logger


class ScreenshotManager(QObject):
    screenshot_taken = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int, bool)
    capture_error_detected = pyqtSignal()  # Новый сигнал для ошибки захвата

    def __init__(self):
        super().__init__()
        self.save_path = None
        self.screenshot_count = 0
        self.capture_enabled = False
        self.hotkey_enabled = False
        self.hotkey_registered = False
        self._zip_thread = None
        self._consecutive_fullscreen_count = 0  # Счетчик последовательных скриншотов всего экрана
        self.is_capturing = False  # Флаг блокировки
        self.last_capture_time = 0  # Время последнего скриншота
        self.min_interval = config.min_interval  # Минимальный интервал между скриншотами
        self.max_screenshots = config.max_screenshots  # Максимальное количество скриншотов
        self.last_delete_time = 0  # Время последнего удаления
        self.delete_cooldown = 2.0  # Задержка 2 секунды между удалениями


    def _thread_safe_status(self, message):
        """Безопасный вызов статуса из любого потока"""
        QMetaObject.invokeMethod(self, "status_changed",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, message))

    def _thread_safe_progress(self, value, visible):
        """Безопасный вызов прогресса из любого потока"""
        QMetaObject.invokeMethod(self, "progress_changed",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(int, value), Q_ARG(bool, visible))

    def _thread_safe_counter(self, count):
        """Безопасный вызов счетчика из любого потока"""
        QMetaObject.invokeMethod(self, "screenshot_taken",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(int, count))

    def _thread_safe_capture_error(self):
        """Безопасный вызов сигнала ошибки захвата"""
        QMetaObject.invokeMethod(self, "capture_error_detected",
                                 Qt.ConnectionType.QueuedConnection)

    def take_screenshot(self):
        """Сделать скриншот с авто-сворачиванием окна"""
        start_time = time.time()
        
        # Защита 1: Проверка параллельного выполнения
        if self.is_capturing:
            logger.warning("Попытка создания скриншота во время активного захвата")
            self.status_changed.emit("Подождите, идет создание скриншота...")
            return

        # Защита 2: Проверка временного интервала
        current_time = time.time()
        time_since_last = current_time - self.last_capture_time
        if time_since_last < self.min_interval:
            remaining = self.min_interval - time_since_last
            logger.debug(f"Слишком быстрый захват, осталось ждать: {remaining:.1f} сек")
            self.status_changed.emit(f"Слишком быстро! Подождите {remaining:.1f} сек")
            return

        # Защита 3: Проверка пути сохранения
        if not self.save_path:
            logger.error("Не выбрана папка для сохранения")
            self.status_changed.emit("Ошибка: не выбрана папка для сохранения")
            return

        # Защита 4: Проверка лимита скриншотов
        if self.screenshot_count >= self.max_screenshots:
            logger.warning(f"Достигнут лимит скриншотов: {self.max_screenshots}")
            self.status_changed.emit(f"Достигнут лимит скриншотов: {self.max_screenshots}")
            return

        should_minimize = not self.capture_enabled and hasattr(self, 'main_window') and self.main_window

        if should_minimize:
            logger.debug("🔄 Сворачиваем окно для скриншота всего экрана...")
            # Используем QTimer для гарантированного выполнения в UI потоке
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.main_window.minimize_window)
            time.sleep(0.01)  # Ждем полного сворачивания

        # Все проверки пройдены - запускаем захват
        logger.info("Начинаем создание скриншота")
        self._actually_take_screenshot()
        
        if should_minimize:
            logger.debug("🔄 Восстанавливаем окно после скриншота...")
            time.sleep(0.01)  # Небольшая задержка перед восстановлением
            # Используем QTimer для гарантированного выполнения в UI потоке
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.main_window.restore_window)

        #Логируем производительность
        durations = time.time() - start_time
        logger.performance("take_csreenshot", durations)

    def _actually_take_screenshot(self):
        """Реальный метод создания скриншота"""
        try:
            self.is_capturing = True
            self.last_capture_time = time.time()

            # Короткая задержка для стабилизации
            time.sleep(0.01)

            # Логика захвата скриншота
            screenshot = None
            if self.capture_enabled:
                screenshot = self.capture_active_window() or self.capture_full_screen()
                mode = "окна" if screenshot and self.capture_enabled else "экрана"
            else:
                screenshot = self.capture_full_screen()
                mode = "экрана"

            if screenshot:
                # Определяем формат и имя файла
                if config.screenshot_format.upper() == "JPEG":
                    filename = f"screenshot_{self.screenshot_count:04d}.jpg"
                    filepath = os.path.join(self.save_path, filename)
                    screenshot.save(filepath, "JPEG", quality=config.screenshot_quality)
                else:
                    filename = f"screenshot_{self.screenshot_count:04d}.png"
                    filepath = os.path.join(self.save_path, filename)
                    screenshot.save(filepath, "PNG")

                self.screenshot_count += 1
                self.screenshot_taken.emit(self.screenshot_count)
                self.status_changed.emit(f"Скриншот {mode} сохранен: {filename}")
                logger.screenshot_taken(filename, mode)
            else:
                logger.error("Не удалось создать скриншот")
                self.status_changed.emit("Не удалось сделать скриншот")

        except Exception as e:
            logger.error(f"Ошибка создания скриншота: {str(e)}")
            self.status_changed.emit(f"Ошибка: {str(e)}")

        finally:
            self.is_capturing = False

    def set_save_path(self, path):
        """Устанавливает путь сохранения с проверкой доступности"""
        try:
            # Проверяем что папка существует и доступна для записи
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

            # Проверяем возможность записи
            test_file = os.path.join(path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)

            self.save_path = path
            self.count_existing_screenshots()
            return True
        except Exception as e:
            print(f"Ошибка установки пути сохранения: {e}")
            return False

    def count_existing_screenshots(self):
        if not self.save_path or not os.path.exists(self.save_path):
            self.screenshot_count = 0
            return

        try:
            png_files = [f for f in os.listdir(self.save_path)
                         if f.startswith('screenshot_') and f.endswith('.png')]

            if png_files:
                numbers = []
                for file in png_files:
                    try:
                        num = int(file[11:-4])
                        numbers.append(num)
                    except ValueError:
                        continue
                self.screenshot_count = max(numbers) + 1 if numbers else 0
            else:
                self.screenshot_count = 0

            self.screenshot_taken.emit(self.screenshot_count)
        except Exception as e:
            print(f"Ошибка подсчета скриншотов: {e}")
            self.screenshot_count = 0

    def get_active_window_rect(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect

            # Используем настройки из конфигурации
            offset_left, offset_top, offset_right, offset_bottom = config.window_capture_offset
            left += offset_left
            top += offset_top
            right += offset_right
            bottom += offset_bottom

            if right > left and bottom > top:
                logger.debug(f"Координаты окна: ({left}, {top}, {right}, {bottom})")
                return (left, top, right, bottom)
            else:
                logger.warning("Некорректные координаты окна")
                return None

        except Exception as e:
            logger.error(f"Ошибка получения координат окна: {e}")
            return None

    def capture_active_window(self):
        try:
            rect = self.get_active_window_rect()
            if not rect:
                return None

            left, top, right, bottom = rect

            if right <= left or bottom <= top:
                return None

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            return screenshot

        except Exception as e:
            print(f"Ошибка захвати активного окна: {e}")
            return None

    def capture_full_screen(self):
        try:
            return ImageGrab.grab()
        except Exception as e:
            print(f"Ошибка захвата экрана: {e}")
            return None

    def start_capture(self):
        self.capture_enabled = True
        self._consecutive_fullscreen_count = 0  # Сбрасываем счетчик при включении
        self.status_changed.emit("Режим захвата активного окна включен")

    def stop_capture(self):
        self.capture_enabled = False
        self._consecutive_fullscreen_count = 0  # Сбрасываем счетчик при выключении
        self.status_changed.emit("Режим захвата активного окна выключен")

    def enable_hotkey(self):
        if self.hotkey_enabled:
            return

        self.hotkey_enabled = True
        try:
            # Регистрируем глобальный обработчик
            keyboard.hook(self._keyboard_event_handler)
            
            self.hotkey_registered = True
            self.status_changed.emit("Горячие клавиши активны (игнорируется numpad)")
        except Exception as e:
            logger.error(f"Ошибка включения горячих клавиш: {str(e)}")
            self.status_changed.emit(f"Ошибка включения горячих клавиш: {str(e)}")
            self.hotkey_enabled = False

    def _keyboard_event_handler(self, event):
        """Глобальный обработчик клавиатуры с фильтрацией numpad"""
        if event.event_type != keyboard.KEY_DOWN or not self.hotkey_enabled:
            return
        
        # Игнорируем все numpad клавиши
        numpad_keys = {
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'num 0', 'num 1', 'num 2', 'num 3', 'num 4', 'num 5', 
            'num 6', 'num 7', 'num 8', 'num 9', 'num .', 'num del'
        }
        
        if event.name in numpad_keys:
            return
        
        # Обрабатываем горячие клавиши
        if event.name == 'insert':
            logger.info("Insert - создание скриншота")
            threading.Thread(target=self.take_screenshot, daemon=True).start()
        
        elif event.name == 'delete':
            logger.info("Delete - удаление скриншота")
            self._delete_hotkey_callback()
        
        elif event.name == 'print screen':
            logger.info("Print Screen - создание скриншота")
            threading.Thread(target=self.take_screenshot, daemon=True).start()

    def delete_last_screenshot(self):
        """Удаляет последний сделанный скриншот"""
        try:
            # ПРОВЕРЯЕМ ЗАДЕРЖКУ
            current_time = time.time()
            time_since_last_delete = current_time - self.last_delete_time
            
            if time_since_last_delete < self.delete_cooldown:
                remaining = self.delete_cooldown - time_since_last_delete
                logger.warning(f"Слишком частое удаление! Подождите {remaining:.1f} сек")
                self.status_changed.emit(f"Подождите {remaining:.1f} сек перед следующим удалением")
                return False

            if self.screenshot_count <= 0 or not self.save_path:
                logger.warning("Нет скриншотов для удаления")
                self.status_changed.emit("Нет скриншотов для удаления")
                return False
            
            # Определяем номер последнего скриншота (count-1 потому что счетчик уже увеличен)
            last_screenshot_number = self.screenshot_count - 1
            
            # Формируем имя последнего файла
            if config.screenshot_format.upper() == "JPEG":
                filename = f"screenshot_{last_screenshot_number:04d}.jpg"
            else:
                filename = f"screenshot_{last_screenshot_number:04d}.png"
                
            filepath = os.path.join(self.save_path, filename)
            
            # Проверяем существование файла и удаляем
            if os.path.exists(filepath):
                os.remove(filepath)
                self.screenshot_count -= 1
                self.screenshot_taken.emit(self.screenshot_count)
                self.last_delete_time = current_time
                logger.info(f"Удален последний скриншот: {filename}")
                self.status_changed.emit(f"Удален скриншот: {filename}")
                return True
            else:
                logger.warning(f"Файл для удаления не найден: {filepath}")
                self.status_changed.emit("Файл для удаления не найден")
                return False
                
        except Exception as e:
            error_msg = f"Ошибка удаления последнего скриншота: {e}"
            logger.error(error_msg)
            self.status_changed.emit(error_msg)
            return False

    def disable_hotkey(self):
        self.hotkey_enabled = False
        try:
            keyboard.unhook_all()
            self.hotkey_registered = False
        except:
            pass
        self.status_changed.emit("Горячие клавиши выключены")

    def _hotkey_callback(self):
        if self.hotkey_enabled:
            threading.Thread(target=self.take_screenshot, daemon=True).start()
    
    def _delete_hotkey_callback(self):
        """Обработчик горячей клавиши Delete для удаления последнего скриншота"""
        logger.debug("Клавиша Delete нажата")
        
        # Проверяем, включен ли режим удаления через главное окно
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'delete_last_checkbox') and self.main_window.delete_last_checkbox.isChecked():
                # ПРОВЕРЯЕМ ЗАДЕРЖКУ
                current_time = time.time()
                time_since_last_delete = current_time - self.last_delete_time
                
                if time_since_last_delete < self.delete_cooldown:
                    remaining = self.delete_cooldown - time_since_last_delete
                    logger.debug(f"Удаление заблокировано, осталось: {remaining:.1f} сек")
                    self.status_changed.emit(f"⏳ Подождите {remaining:.1f} сек")
                    return

                logger.info("Удаление последнего скриншота по Delete")
                threading.Thread(target=self.delete_last_screenshot, daemon=True).start()
            else:
                # Если чекбокс выключен, просто игнорируем нажатие Delete
                logger.debug("Режим удаления отключен - игнорируем Delete")
                self.status_changed.emit("❌ Включите 'Delete для удаления' в настройках")
        else:
            # Если нет доступа к UI, проверяем задержку и удаляем
            current_time = time.time()
            time_since_last_delete = current_time - self.last_delete_time
            
            if time_since_last_delete < self.delete_cooldown:
                remaining = self.delete_cooldown - time_since_last_delete
                logger.debug(f"Удаление заблокировано, осталось: {remaining:.1f} сек")
                self.status_changed.emit(f"⏳ Подождите {remaining:.1f} сек")
                return
            
            logger.info("Удаление последнего скриншота по Delete (без проверки UI)")
            threading.Thread(target=self.delete_last_screenshot, daemon=True).start()

    def _register_delete_hotkey(self):
        """Регистрирует горячую клавишу Delete"""
        try:
            keyboard.add_hotkey('delete', self._delete_hotkey_callback, suppress=True)
            logger.info("Горячая клавиша Delete зарегистрирована")
        except Exception as e:
            logger.error(f"Ошибка регистрации Delete: {e}")

    def cleanup(self):
        self.stop_capture()
        self.disable_hotkey()
        try:
            keyboard.clear_all_hotkeys()
        except:
            pass
        if self._zip_thread and self._zip_thread.is_alive():
            self._zip_thread.join(timeout=1.0)