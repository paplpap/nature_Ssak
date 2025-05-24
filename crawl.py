# 안전신문고 용 크롤러  43쌍의 QA데이터 수집
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from time import sleep
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 안전신문고 접속
driver.get("https://www.safetyreport.go.kr/#main/search/%EB%AC%B4%EB%8B%A8%ED%88%AC%EA%B8%B0")


def collect_page():
    results = []

    items = driver.find_elements(By.XPATH, '''//*[@id="result_list"]/li[contains(@class, 'result_subject')]''')

    for idx, item in enumerate(items):
        try:
            print(f"{idx+1}번째 항목 클릭 중...")

            item.click()
            sleep(1)

            content = driver.find_element(By.XPATH, '//*[@id="C_A_CONTENTS"]')  # 수정 필요시 XPath로 바꿔도 됨
            content2 = driver.find_element(By.XPATH, '//*[@id="grid_answer"]/table[1]/tbody/tr[2]/td')  # 수정 필요시 XPath로 바꿔도 됨
            text = content.text.strip()
            print(text[:20])
            text2 = content2.text.strip()

            with open("safety_memo.txt", "a", encoding="utf-8") as f:
                f.write(text + "\n\n")
                f.write(text2 + "\n\n")

            x_button = driver.find_element(By.XPATH, '''//*[@id="div_modalPopup"]/div/div/div[1]/button''')  # 예시용 CSS
            x_button.click()
            sleep(1)

            items = driver.find_elements(By.XPATH, '''//*[@id="result_list"]/li[contains(@class, 'result_subject')]''')



        except Exception as e:
            print(f"{idx+1}번 실패: {e}")
            continue

# 페이지 번호를 클릭하는 함수
def click_page(page_number: int):
    try:
        xpath = f'//a[text()="{page_number}" and @title="페이징"]'
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        button.click()
        sleep(1)
        print(f"{page_number} 페이지 클릭 성공")
    except Exception as e:
        print(f"{page_number} 페이지 클릭 실패: {e}")

for block in range(0, 5):
    paging_value = block * 10
    print(f"doPaging('{paging_value}') 실행 중...")
    driver.execute_script(f"doPaging('{paging_value}')")
    sleep(1)

    # 이후 페이지 내에서 1~10 클릭 루프 수행 가능
    collect_page()  # 목록 수집



# 종료
#driver.quit()

# 저장
# with open("safety_report.txt", "w", encoding="utf-8") as f:
#     for item in results:
#         f.write(item + "\n\n")
