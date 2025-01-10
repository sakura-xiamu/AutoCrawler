from urllib.parse import urlparse
import os


class LinkFilter:
    def __init__(self, domains_file='filtered_domains.txt'):
        self.domains_file = domains_file
        self.filtered_domains = self.load_domains()

    def load_domains(self):
        """从文件加载过滤域名"""
        if not os.path.exists(self.domains_file):
            print(f"警告: 域名文件 '{self.domains_file}' 不存在")
            return set()

        try:
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = {
                    line.strip().lower()
                    for line in f
                    if line.strip() and not line.startswith('#')  # 忽略注释行
                }
            print(f"成功加载 {len(domains)} 个过滤域名")
            return domains
        except Exception as e:
            print(f"读取域名文件时出错: {str(e)}")
            return set()

    def reload_domains(self):
        """重新加载域名列表"""
        self.filtered_domains = self.load_domains()

    def add_domain(self, domain):
        """添加新的过滤域名到文件和内存"""
        domain = domain.strip().lower()
        if domain not in self.filtered_domains:
            try:
                with open(self.domains_file, 'a', encoding='utf-8') as f:
                    f.write(f'\n{domain}')
                self.filtered_domains.add(domain)
                print(f"成功添加域名: {domain}")
            except Exception as e:
                print(f"添加域名时出错: {str(e)}")

    def remove_domain(self, domain):
        """从文件和内存中移除过滤域名"""
        domain = domain.strip().lower()
        if domain in self.filtered_domains:
            self.filtered_domains.remove(domain)
            try:
                # 重写文件
                with open(self.domains_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(sorted(self.filtered_domains)))
                print(f"成功移除域名: {domain}")
            except Exception as e:
                print(f"移除域名时出错: {str(e)}")
                # 恢复内存中的域名
                self.filtered_domains.add(domain)

    def check_link(self, link):
        """检查链接是否应该被过滤"""
        try:
            domain = urlparse(link).netloc.lower()
            return not any(filtered_domain in domain for filtered_domain in self.filtered_domains)
        except Exception as e:
            print(f"检查链接时出错 ({link}): {str(e)}")
            return False

    def filter_links(self, links):
        """过滤链接列表"""
        filtered = []
        filtered_count = 0
        for link in links:
            if self.check_link(link):
                filtered.append(link)
            else:
                filtered_count += 1
        print('一共过滤了{}各域名'.format(filtered_count))
        return filtered

    def print_domains(self):
        """打印当前所有过滤域名"""
        print("\n当前过滤域名列表:")
        for domain in sorted(self.filtered_domains):
            print(f"- {domain}")


if __name__ == '__main__':
    # 创建过滤器实例
    filter = LinkFilter('filtered_domains.txt')

    # 打印当前过滤域名
    filter.print_domains()

    # 测试链接列表
    links = [
        'https://www.example.com/image1.jpg',
        'https://dreamstime.com/image2.jpg',
        'https://alamy.com/image3.jpg',
        'https://mysite.com/image4.jpg'
    ]

    # 过滤链接
    filtered_links = filter.filter_links(links)

    print("\n过滤后的链接:")
    for link in filtered_links:
        print(link)

    # 示例：添加新域名
    # filter.add_domain('newdomain.com')

    # 示例：移除域名
    # filter.remove_domain('dreamstime.com')

    # 示例：重新加载域名列表
    # filter.reload_domains()
