import random
import time


class ScrollDetector:
    def __init__(self, driver):
        self.driver = driver
        self.last_height = 0
        self.unchanged_count = 0
        self.max_unchanged = 3  # 连续相同次数的阈值

    def get_scroll_info(self):
        """获取更可靠的滚动信息"""
        return self.driver.execute_script("""
            return {
                scrollTop: Math.max(
                    document.documentElement.scrollTop,
                    document.body.scrollTop,
                    window.pageYOffset
                ),
                clientHeight: Math.max(
                    document.documentElement.clientHeight,
                    window.innerHeight
                ),
                scrollHeight: Math.max(
                    document.documentElement.scrollHeight,
                    document.body.scrollHeight,
                    document.documentElement.offsetHeight,
                    document.body.offsetHeight
                ),
                offsetHeight: Math.max(
                    document.documentElement.offsetHeight,
                    document.body.offsetHeight
                )
            };
        """)

    def is_bottom_reached(self, threshold=50):
        """
        检查是否到达底部
        threshold: 距离底部的像素阈值
        """
        try:
            scroll_info = self.get_scroll_info()
            current_position = scroll_info['scrollTop'] + scroll_info['clientHeight']
            total_height = scroll_info['scrollHeight']

            # 检查高度是否变化
            if abs(total_height - self.last_height) < 1:
                self.unchanged_count += 1
            else:
                self.unchanged_count = 0
                self.last_height = total_height

            # 多重判断
            is_bottom = (
                # 传统方法：检查是否接近底部
                    (total_height - current_position <= threshold) or
                    # 检查是否连续多次高度未变化
                    (self.unchanged_count >= self.max_unchanged) or
                    # 检查是否已经超过文档高度
                    (current_position >= total_height)
            )

            return is_bottom

        except Exception as e:
            print(f"Error checking scroll position: {e}")
            return False

    def scroll_to_bottom(self, scroll_pause_time=1.0):
        """
        渐进式滚动到底部
        """
        try:
            while not self.is_bottom_reached():
                # 获取当前滚动位置
                current_scroll = self.get_scroll_info()['scrollTop']

                # 计算下一次滚动的距离（随机化）
                scroll_step = random.randint(300, 700)

                # 平滑滚动
                self.driver.execute_script(
                    f"window.scrollTo({{top: {current_scroll + scroll_step}, behavior: 'smooth'}});"
                )

                # 随机等待时间
                time.sleep(random.uniform(scroll_pause_time * 0.8, scroll_pause_time * 1.2))

                # 检查是否有新内容加载
                self.wait_for_content_change()

        except Exception as e:
            print(f"Error during scrolling: {e}")

    def wait_for_content_change(self, timeout=5):
        """等待内容变化"""
        try:
            initial_height = self.get_scroll_info()['scrollHeight']
            start_time = time.time()

            while time.time() - start_time < timeout:
                current_height = self.get_scroll_info()['scrollHeight']
                if current_height != initial_height:
                    # 内容已更新，等待它稳定
                    time.sleep(0.5)
                    return True
                time.sleep(0.1)

            return False

        except Exception as e:
            print(f"Error waiting for content change: {e}")
            return False

    def get_page_state(self):
        """获取页面状态的详细信息"""
        try:
            return self.driver.execute_script("""
                return {
                    pageYOffset: window.pageYOffset,
                    scrollY: window.scrollY,
                    scrollTop: document.documentElement.scrollTop,
                    bodyScrollTop: document.body.scrollTop,
                    clientHeight: document.documentElement.clientHeight,
                    innerHeight: window.innerHeight,
                    scrollHeight: document.documentElement.scrollHeight,
                    bodyScrollHeight: document.body.scrollHeight,
                    offsetHeight: document.documentElement.offsetHeight,
                    bodyOffsetHeight: document.body.offsetHeight,
                    documentHeight: Math.max(
                        document.body.scrollHeight,
                        document.body.offsetHeight,
                        document.documentElement.clientHeight,
                        document.documentElement.scrollHeight,
                        document.documentElement.offsetHeight
                    )
                };
            """)
        except Exception as e:
            print(f"Error getting page state: {e}")
            return None
