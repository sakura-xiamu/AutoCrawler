from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import random
import time


class ElementMover:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.actions = ActionChains(driver)

    def get_viewport_size(self):
        """获取浏览器视窗大小"""
        return {
            'width': self.driver.execute_script('return window.innerWidth;'),
            'height': self.driver.execute_script('return window.innerHeight;')
        }

    def is_in_viewport(self, element):
        """检查元素是否在视窗内"""
        return self.driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        """, element)

    def scroll_element_into_center(self, element):
        """将元素滚动到视窗中央"""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
            element
        )
        time.sleep(0.5)  # 等待滚动完成

    def safe_move_to_element(self, xpath):
        """安全地移动到元素"""
        try:
            # 等待元素存在
            element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # 确保元素在视窗中央
            self.scroll_element_into_center(element)

            # 获取元素位置和大小
            location = element.location_once_scrolled_into_view
            size = element.size

            # 计算元素中心点
            target_x = size['width'] / 2
            target_y = size['height'] / 2

            # 重置鼠标位置到元素上方
            self.actions.move_to_element(element).perform()

            return element

        except Exception as e:
            print(f"Failed to move to element safely: {e}")
            return None

    def move_to_element_human_like(self, xpath):
        """改进的人性化移动到元素方法"""
        try:
            # 首先安全地移动到元素
            element = self.safe_move_to_element(xpath)
            if not element:
                return False

            # 确保元素可见
            if not element.is_displayed():
                print("Element is not visible")
                return False

            # 获取视窗大小
            viewport = self.get_viewport_size()

            # 获取元素位置
            rect = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                };
            """, element)

            # 计算安全的移动范围
            safe_x = min(max(rect['left'], 0), viewport['width'] - 1)
            safe_y = min(max(rect['top'], 0), viewport['height'] - 1)

            # 分步移动到目标位置
            current_x = viewport['width'] / 2  # 从视窗中心开始
            current_y = viewport['height'] / 2

            steps = random.randint(3, 5)
            for i in range(steps):
                # 计算下一个点，确保在视窗内
                next_x = current_x + (safe_x - current_x) * (i + 1) / steps
                next_y = current_y + (safe_y - current_y) * (i + 1) / steps

                # 添加小幅随机偏移
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)

                # 确保偏移后的位置仍在视窗内
                next_x = min(max(0, next_x + offset_x), viewport['width'] - 1)
                next_y = min(max(0, next_y + offset_y), viewport['height'] - 1)

                # 计算相对移动距离
                move_x = next_x - current_x
                move_y = next_y - current_y

                # 执行移动
                self.actions.move_by_offset(move_x, move_y).perform()

                # 更新当前位置
                current_x = next_x
                current_y = next_y

                # 添加随机延迟
                time.sleep(random.uniform(0.1, 0.2))

            # 最后精确移动到元素
            self.actions.move_to_element(element).perform()
            return True

        except Exception as e:
            print(f"Failed to move to element with human-like motion: {e}")
            return False

    def click_element_safely(self, xpath):
        """安全的点击操作"""
        try:
            # 首先移动到元素
            if not self.move_to_element_human_like(xpath):
                return False

            # 等待元素可点击
            element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

            # 随机延迟
            time.sleep(random.uniform(0.1, 0.3))

            # 尝试点击
            try:
                element.click()
            except:
                # 如果普通点击失败，尝试JavaScript点击
                self.driver.execute_script("arguments[0].click();", element)

            return True

        except Exception as e:
            print(f"Failed to click element safely: {e}")
            return False
