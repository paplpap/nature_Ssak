import requests


def get_waste_stats(pid: str, year: str, user_id: str, api_key: str) -> dict:
    base_url = "https://www.recycling-info.or.kr/sds/JsonApi.do"
    params = {
        "PID": pid,
        "YEAR": year,
        "USRID": user_id,
        "KEY": api_key
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # 오류 코드 확인
        result_info = data.get("result", [{}])[0]
        if result_info.get("ERR_CODE") != "E000":
            return {"error": f"API 오류: {result_info.get('RESULT')}"}

        return data
    except Exception as e:
        return {"error": str(e)}

# 호출 예시
#pid = "NTN012"              # PPP019 (실제 민원 범주형 분류),,NTN012 (지역+폐기물차량 현황),,
year = "2022"


def filter_region_data_from_api(json_data: dict, region_name: str) -> list:
    """
    DURL API 응답에서 지정한 지역명(자치구)에 해당하는 데이터만 필터링하여 반환합니다.

    Args:
        json_data (dict): API 응답 전체 JSON
        region_name (str): 예: "강남구", "마포구"

    Returns:
        list: 해당 지역의 데이터만 포함된 리스트 (없으면 빈 리스트)
    """
    try:
        data_list = json_data.get("data", [])
        # CTS_JIDT_NM이 정확히 일치하는 데이터만 필터링
        region_data = [item for item in data_list if item.get("CTS_JIDT_NM") == region_name]
        return region_data
    except Exception as e:
        print(f"[ERROR] 지역 데이터 필터링 중 오류 발생: {e}")
        return []


def filter_cts_region_data_from_ntn012(json_data: dict, region_name: str) -> list:
    """
    NTN012 API 응답에서 특정 시군구(region_name)에 해당하는 항목만 필터링합니다.

    Args:
        json_data (dict): DURL API의 JSON 응답
        region_name (str): 예: "강남구", "강서구", "제주시"

    Returns:
        list: 필터된 지역 데이터 목록 (없으면 빈 리스트)
    """
    try:
        data_list = json_data.get("data", [])
        region_data = [item for item in data_list if item.get("CTS_JIDT_CD_NM") == region_name]
        return region_data
    except Exception as e:
        print(f"[ERROR] NTN012 지역 필터링 오류: {e}")
        return []


def nature_api(location :str):

    result = get_waste_stats("PPP019", year, user_id, api_key)

    filtered1 = filter_region_data_from_api(result, location)

    result = get_waste_stats("NTN012", year, user_id, api_key)

    filtered2= filter_cts_region_data_from_ntn012(result, location)

    answer = []
    answer1 = []

    for entry in filtered1:
        answer.append(entry)

    for entry in filtered2:
        answer1.append(entry)

    return answer, answer1


SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구",
    "종로구", "중구", "중랑구"
]

def extract_seoul_district(text: str) -> str:
    """
    입력된 사용자 텍스트에서 서울시 자치구명을 추출합니다.

    Args:
        text (str): 사용자 입력 예: "강남구에 쓰레기 무단투기가 많아요"

    Returns:
        str: 발견된 자치구명 (예: "강남구") 또는 None
    """
    for gu in SEOUL_DISTRICTS:
        if gu in text:
            complaint_data, vehicle_data =  nature_api(gu)
            ans = summarize_region_insight(text, complaint_data, vehicle_data)
            return ans
        else:
            None


def summarize_region_insight(region_name: str, complaint_data: list, vehicle_data: list) -> str:
    """
    민원 신고 통계 + 차량 현황 데이터를 자연어 요약문으로 변환

    Args:
        region_name (str): 예: "강남구"
        complaint_data (list): PPP019 필터링 결과
        vehicle_data (list): NTN012 필터링 결과

    Returns:
        str: LLM에 넣기 적합한 지역 기반 통계 요약 문장
    """
    #  민원 신고 요약
    complaint_section = ""
    for entry in complaint_data:
        if entry.get("TY_NM") in ["소계", "쓰레기·담배꽁초등무단투기"]:
            total_reports = entry.get("STTEMNT_CO", 0)
            fines_issued = entry.get("FFNLG_LEVY_CO", 0)
            total_fine_amount = entry.get("FFNLG_LEVY_AMOUNT", 0)
            unpaid_cases = entry.get("FFNLG_NPY_CO", 0)
            reward_cases = entry.get("RWARD_MNY_PYMNT_CO", 0)

            complaint_section = (
                f"{region_name}는 무단투기 및 담배꽁초 관련 민원이 연간 {total_reports}건 접수되며, "
                f"그중 {fines_issued}건에 대해 총 {total_fine_amount}천원의 과태료가 부과되었습니다. "
                f"하지만 {unpaid_cases}건은 미납 상태이며, 시민 신고에 따른 포상금은 {reward_cases}건 지급되었습니다."
            )
            break

    #  차량 보유 현황 요약
    vehicle_section = ""
    for v in vehicle_data:
        if v.get("USG_GB_NM") == "생활폐기물":
            total_vehicles = v.get("TOT_SUM", 0)
            sticker_trucks = v.get("STICK_CAR", 0)
            tank_lorries = v.get("TANK_MAX_LORRY", 0)
            cargo_trucks = v.get("CARGO_MAX_CAR", 0)
            dump_trucks = v.get("DMPT_MAX_TRUCK", 0)
            etc_vehicles = v.get("ETC_MAX", 0)

            vehicle_section = (
                f"또한 {region_name}는 생활폐기물 수거를 위해 총 {total_vehicles}대의 차량을 운영 중이며, "
                f"스티커 수거차 {sticker_trucks}대, 탱크로리 {tank_lorries}대, 적재차 {cargo_trucks}대, "
                f"덤프트럭 {dump_trucks}대, 기타 차량 {etc_vehicles}대가 포함되어 있습니다."
            )
            break

    #  결합
    if complaint_section or vehicle_section:
        return f"{region_name} 지역 통계 요약\n- {complaint_section}\n- {vehicle_section}"
    else:
        return f"{region_name}의 민원 및 차량 정보가 충분하지 않아 통계 요약을 제공하지 못했습니다."

if __name__ == "__main__":
    extract_seoul_district('강남구에 쓰래기 대량 발생')

