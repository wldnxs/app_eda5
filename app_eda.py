import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population Trends 데이터셋**  
                - 설명: 2008–2023년 대한민국 지역별 인구 수 변화 기록한 데이터  
                - 주요 변수:  
                  - `year`: 연도
                  - `city`: 지역 
                  - `population`: 인구  
                  - `birth`: 출생아수
                  - `death`: 사망자수
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:

            # '세종' 지역 데이터만 필터링
            sejong_df = df[df['지역'].str.contains('세종', na=False)].copy()

            # 숫자열로 변환
            numeric_columns = ['인구', '출생아수(명)', '사망자수(명)']
            for col in numeric_columns:
                sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0)

            st.subheader("데이터프레임 구조 (info)")
            buffer = io.StringIO()
            sejong_df.info(buf=buffer)
            info_str = buffer.getvalue()
            st.text(info_str)

            st.subheader("데이터 요약 통계 (describe)")
            st.dataframe(sejong_df.describe())


        # 2. 연도별 추이이
        with tabs[1]:

            # 숫자형으로 변환
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # '전국' 데이터만 필터링
            national_df = df[df['지역'].str.contains('전국', na=False)].copy()
            national_df.sort_values(by='연도', inplace=True)

            # 기본 인구 추이 그래프용 데이터
            years = national_df['연도'].astype(int)
            population = national_df['인구']

            # 최근 3년 평균 출생/사망 수로 인구 변화율 예측
            recent_data = national_df.tail(3)
            avg_births = recent_data['출생아수(명)'].mean()
            avg_deaths = recent_data['사망자수(명)'].mean()
            annual_net_change = avg_births - avg_deaths

            # 2035년 예측
            last_year = years.max()
            last_population = population.iloc[-1]
            years_ahead = 2035 - last_year
            predicted_pop_2035 = last_population + annual_net_change * years_ahead

            # 예측치 포함한 시계열 생성
            extended_years = list(years) + [2035]
            extended_population = list(population) + [predicted_pop_2035]

            # 그래프 생성
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(extended_years, extended_population, marker='o', label='Population')
            ax.axvline(x=2035, linestyle='--', color='red', label='2035 Forecast')
            ax.annotate(f'{int(predicted_pop_2035):,}', xy=(2035, predicted_pop_2035),xytext=(2030, predicted_pop_2035 + 200000),arrowprops=dict(facecolor='red', shrink=0.05),fontsize=9)

            ax.set_title('Population Trend Forecast')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend()
            ax.grid(True)
        
            st.pyplot(fig)

        # 3. 지역별 분석
        with tabs[2]:
            # 한글 지역명 → 영어로 변환하는 딕셔너리 (예시)
            region_translation = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi',
            '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk',
            '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }

            st.title("Population Change by Region (Last 5 Years)")



            # 숫자 변환
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')

            # 전국 제외
            region_df = df[df['지역'] != '전국'].copy()

            # 지역별 최신 5개 연도 인구 변화 계산
            change_data = []

            for region in region_df['지역'].unique():
                temp = region_df[region_df['지역'] == region].sort_values('연도')
                if len(temp) >= 5:
                    recent = temp.tail(5)
                    change = recent['인구'].iloc[-1] - recent['인구'].iloc[0]
                    percent_change = (change / recent['인구'].iloc[0]) * 100 if recent['인구'].iloc[0] > 0 else 0
                    change_data.append({
                        'Region_KR': region,
                        'Region_EN': region_translation.get(region, region),
                        'Change': change / 1000,  # 천명 단위
                        'PercentChange': percent_change
                    })

            change_df = pd.DataFrame(change_data)
            change_df.sort_values('Change', ascending=False, inplace=True)

            # ------------------ 변화량 그래프 ------------------
            st.subheader("Change in Population (Last 5 Years)")

            fig1, ax1 = plt.subplots(figsize=(10, 7))
            sns.barplot(data=change_df, y='Region_EN', x='Change', ax=ax1, palette='viridis')
            ax1.set_title("Population Change by Region", fontsize=14)
            ax1.set_xlabel("Population Change (thousands)")
            ax1.set_ylabel("")

            # 값 표시
            for index, row in change_df.iterrows():
                ax1.text(row['Change'] + 2, index, f"{row['Change']:.1f}", va='center')

            st.pyplot(fig1)

            # ------------------ 변화율 그래프 ------------------
            st.subheader("Population Growth Rate (%)")

            change_df.sort_values('PercentChange', ascending=False, inplace=True)

            fig2, ax2 = plt.subplots(figsize=(10, 7))
            sns.barplot(data=change_df, y='Region_EN', x='PercentChange', ax=ax2, palette='coolwarm')
            ax2.set_title("Population Growth Rate by Region", fontsize=14)
            ax2.set_xlabel("Growth Rate (%)")
            ax2.set_ylabel("")

            for index, row in change_df.iterrows():
                ax2.text(row['PercentChange'] + 0.2, index, f"{row['PercentChange']:.1f}%", va='center')

            st.pyplot(fig2)

            # ------------------ 해설 ------------------
            st.markdown("### Interpretation")
            top_region = change_df.iloc[0]
            bottom_region = change_df.iloc[-1]
            st.markdown(f"""
            - **{top_region['Region_EN']}** shows the highest population growth over the past 5 years (**+{top_region['Change']:.1f}k**, {top_region['PercentChange']:.1f}%).
            - **{bottom_region['Region_EN']}** has the steepest decline (**{bottom_region['Change']:.1f}k**, {bottom_region['PercentChange']:.1f}%).
            - The results reflect regional trends in urbanization, birth/death rates, and migration.
            """)

        # 4. 변화량 분석
        with tabs[3]:

            # 숫자형 변환
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')

            # 전국 제외
            region_df = df[df['지역'] != '전국'].copy()

            # 연도별 인구 증감(diff)
            region_df.sort_values(['지역', '연도'], inplace=True)
            region_df['인구증감'] = region_df.groupby('지역')['인구'].diff()

            # 증감 상위 100개 추출 (절댓값 기준)
            top_diff_df = region_df.dropna(subset=['인구증감']).copy()
            top_diff_df['인구증감_abs'] = top_diff_df['인구증감'].abs()
            top100 = top_diff_df.sort_values('인구증감_abs', ascending=False).head(100)

            # 천단위 콤마 포맷
            def format_number(val):
                return f"{int(val):,}"

            styled_df = top100[['연도', '지역', '인구', '인구증감']].copy()
            styled_df['인구'] = styled_df['인구'].apply(format_number)
            styled_df['인구증감'] = styled_df['인구증감'].apply(lambda x: f"{int(x):,}")

            # 컬러바 스타일 적용
            def color_gradient(val):
                try:
                    val = int(val.replace(',', ''))
                    base = 1_000_000  # 컬러 스케일 기준
                    if val > 0:
                        # 파랑 계열: 증가
                        return f"background-color: rgba(0, 100, 255, {min(0.9, abs(val)/base)})"
                    else:
                        # 빨강 계열: 감소
                        return f"background-color: rgba(255, 0, 0, {min(0.9, abs(val)/base)})"
                except:
                    return ""

            st.subheader("Top 100 Population Change Cases")
            
            st.dataframe(
                styled_df.style.applymap(color_gradient, subset=['인구증감']),
                use_container_width=True
            )
        # 5. 시각화
        with tabs[4]:
            st.title("Regional Population Stacked Area Chart")

            # 한글 지역명 → 영문 매핑
            region_translation = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi',
                '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk',
                '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }


            # 숫자형 변환
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    
            # 전국 제외 및 영문 지역명으로 변환
            df = df[df['지역'] != '전국'].copy()
            df['Region_EN'] = df['지역'].map(region_translation)

            # 피벗 테이블 생성: 연도 = index, 지역 = columns, 값 = 인구
            pivot_df = df.pivot_table(index='연도', columns='Region_EN', values='인구', aggfunc='sum')

            # 연도 기준 정렬 및 결측치 0으로 대체
            pivot_df = pivot_df.sort_index().fillna(0)

            # 그래프 그리기
            st.subheader("Stacked Area Chart of Regional Population")
    
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df = pivot_df / 1000  # 천 단위로 축소

            colors = sns.color_palette("tab20", n_colors=len(pivot_df.columns))
            pivot_df.plot(kind='area', stacked=True, ax=ax, color=colors)

            ax.set_title("Population Trend by Region", fontsize=14)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population (thousands)")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), title="Region")
            ax.grid(True)

            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()