import os
import requests
import re
from github import Github
from bs4 import BeautifulSoup

# 配置信息
GITHUB_TOKEN = os.environ['my_api_token']
REPO_NAME = 'DedeCMS'
OWNER = 'PrinceFPF'

chrome_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
headers = {
    'User-Agent': chrome_user_agent
}
proxy = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

def fetch_download_info():
    """
    获取最新版本的下载链接和MD5信息
    :return: 下载地址、文件名、版本号、MD5值
    """
    file_md5 = ''
    download_url = ''
    file_name = ''
    version = ''
    base_url = "https://www.dedecms.com/download"
    response = requests.get(base_url, headers=headers, timeout=3)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1.定位含有"MD5 HASH"的<p>标签
        p_tag = soup.find('p', string=lambda text: 'MD5 HASH' in text)
        if p_tag:
            file_md5 = p_tag.get_text()[:32]
        else:
            print("没有找到文件MD5信息.")

        # 2.定位下载地址
        a_tag = soup.select_one('a.btn-primary')
        if a_tag:
            # 获取href属性
            href_value = a_tag.get('href')
            download_url = href_value
            file_name = download_url.split('/')[-1]
            version = 'V' + re.search(r'V(\d+\.\d+\.\d+)', file_name).group(1)
        else:
            print("没有找到下载地址.")
    else:
        print("没有获取到网页内容.")

    return download_url, file_name, version, file_md5


def upload_release_asset(download_url, file_name, version, file_md5):
    # 下载安装包
    response = requests.get(download_url, headers=headers)
    if response.status_code == 200:
        # 下载安装包
        with open(file_name, 'wb') as f:
            f.write(response.content)
        # 生成 MD5 文件
        with open('MD5.txt', 'wb') as f_md5:
            f_md5.write(file_md5.encode('utf-8'))
    else:
        print('Failed to download the package.')
        exit(1)


    # 使用PyGithub创建GitHub Release
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(f'{OWNER}/{REPO_NAME}')

    # 检查是否已存在相同版本的Release
    releases = repo.get_releases()
    existing_release = None
    for release in releases:
        if release.tag_name == version:
            existing_release = release
            break

    if existing_release:
        print(f'Release {version} already exists. Skipping upload.')
    else:
        # 创建Release需要提供tag_name, name和message参数
        release_message = f'Release DedeCMS version {version}'
        # 创建Release
        release = repo.create_git_release(tag=version, name=f'DedeCMS {version}', message=release_message, draft=False)

        # 上传Release Asset
        release.upload_asset(file_name, f'DedeCMS{version}')
        release.upload_asset('MD5.txt', 'MD5.txt')
        print(f'Release {version} has been created and the package has been uploaded.')

    # 清理下载的文件
    os.remove(file_name)
    os.remove('MD5.txt')

if __name__ == "__main__":
    download_url, file_name, version, file_md5 = fetch_download_info()
    upload_release_asset(download_url, file_name, version, file_md5)
