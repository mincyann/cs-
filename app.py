from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.case_store import list_reviewed_cases, save_reviewed_case
from src.classify import classify_issue_response, load_categories
from src.email_draft import build_email_draft
from src.result_store import append_classification_result, update_latest_final_category as update_latest_csv_category
from src.sample_data import DEFAULT_SYNTHETIC_EXCEL, load_sample_cases
from src.transcript_extract import extract_issue_response


ROOT = Path(__file__).resolve().parent
CATEGORIES_PATH = ROOT / "data" / "categories.json"
SAMPLE_JSON_PATH = ROOT / "data" / "sample_cases.json"
RESULTS_CSV_PATH = ROOT / "data" / "feedback" / "classification_results.csv"
CASE_DB_PATH = ROOT / "data" / "reviewed_cases.db"
DEMO_TRANSCRIPT = """고객: 앱에서 검사 업로드가 계속 멈추고 결과지가 웹에서 바로 확인되지 않습니다.
상담사: 네트워크 상태 확인과 앱 재실행을 안내했고, 웹 결과지는 브라우저 새로고침 후 다시 확인해 보시도록 안내했습니다."""


def load_styles():
    st.markdown(
        """
        <style>
        :root {
            --ink: #17352d;
            --muted: #64766f;
            --line: #dfe8e3;
            --panel: #ffffff;
            --soft: #f5faf7;
            --brand: #174f3f;
            --brand-2: #2f7d66;
            --accent: #0ea5a3;
            --warn: #b45309;
        }

        .stApp {
            background:
                linear-gradient(180deg, #f7fbf8 0%, #eef6f2 38%, #f7faf9 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 2.1rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 10px 24px rgba(23, 53, 45, 0.06);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.82rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.25rem;
        }

        .console-header {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: flex-start;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 22px 24px;
            box-shadow: 0 18px 36px rgba(23, 53, 45, 0.08);
            margin-bottom: 16px;
        }

        .eyebrow {
            color: var(--brand-2);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            margin-bottom: 6px;
        }

        .console-title {
            color: var(--ink);
            font-size: 1.85rem;
            line-height: 1.2;
            font-weight: 800;
            margin: 0 0 8px 0;
        }

        .console-subtitle {
            color: var(--muted);
            font-size: 0.95rem;
            margin: 0;
            max-width: 760px;
        }

        .mode-pill {
            border: 1px solid #b7dfcf;
            background: #e7f7ef;
            color: #14543f;
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.82rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .section-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(23, 53, 45, 0.06);
            min-height: 100%;
        }

        .section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 12px;
        }

        .section-title h3 {
            font-size: 1rem;
            margin: 0;
            font-weight: 800;
        }

        .section-title span {
            color: var(--muted);
            font-size: 0.78rem;
        }

        .planned-box {
            border: 1px dashed #aacfc0;
            background: #f3fbf7;
            border-radius: 8px;
            padding: 12px 14px;
            color: var(--muted);
            font-size: 0.86rem;
            margin: 10px 0 14px 0;
        }

        .result-hero {
            border: 1px solid #bfe1d4;
            background: linear-gradient(180deg, #f5fffa 0%, #ffffff 100%);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .result-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .result-category {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 850;
            line-height: 1.25;
        }

        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .badge.good {
            background: #dcfce7;
            color: #166534;
            border-color: #bbf7d0;
        }

        .badge.warn {
            background: #ffedd5;
            color: #9a3412;
            border-color: #fed7aa;
        }

        .badge.info {
            background: #e0f2fe;
            color: #075985;
            border-color: #bae6fd;
        }

        .reason-box {
            background: #f7faf8;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px 14px;
            color: #314a42;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .empty-state {
            border: 1px dashed #c7d8d0;
            border-radius: 8px;
            padding: 28px 18px;
            text-align: center;
            color: var(--muted);
            background: #fbfefd;
        }

        div.stButton > button {
            border-radius: 8px;
            border: 1px solid #c9d8d1;
            font-weight: 700;
        }

        div.stButton > button[kind="primary"] {
            background: var(--brand);
            border-color: var(--brand);
            color: #ffffff;
        }

        textarea, input, div[data-baseweb="select"] > div {
            border-radius: 8px !important;
        }

        .history-title {
            margin-top: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .small-note {
            color: var(--muted);
            font-size: 0.82rem;
        }

        @media (max-width: 900px) {
            .console-header {
                flex-direction: column;
            }
            .console-title {
                font-size: 1.5rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    defaults = {
        "issue_text": "",
        "response_text": "",
        "result": None,
        "history": [],
        "final_category": "",
        "transcript_text": "",
        "transcript_status": "",
        "extraction_result": None,
        "email_draft": None,
        "responsible_owner": "",
        "reviewer": "",
        "internal_note": "",
        "review_save_status": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.cache_data(show_spinner=False)
def cached_samples():
    return load_sample_cases(
        sample_json_path=SAMPLE_JSON_PATH,
        synthetic_excel_path=DEFAULT_SYNTHETIC_EXCEL,
        max_cases=5,
    )


@st.cache_data(show_spinner=False)
def cached_category_names():
    return [category.name for category in load_categories(CATEGORIES_PATH)]


def apply_sample(case):
    st.session_state.issue_text = case["issue_text"]
    st.session_state.response_text = case["response_text"]
    st.session_state.result = None
    st.session_state.final_category = case.get("expected_category", "")


def clear_inputs():
    st.session_state.issue_text = ""
    st.session_state.response_text = ""
    st.session_state.result = None
    st.session_state.final_category = ""
    st.session_state.transcript_text = ""
    st.session_state.transcript_status = ""
    st.session_state.extraction_result = None
    st.session_state.email_draft = None
    st.session_state.responsible_owner = ""
    st.session_state.reviewer = ""
    st.session_state.internal_note = ""
    st.session_state.review_save_status = ""


def apply_demo_transcript():
    st.session_state.transcript_text = DEMO_TRANSCRIPT
    st.session_state.extraction_result = None
    st.session_state.result = None
    st.session_state.email_draft = None


def extract_current_transcript():
    extraction = extract_issue_response(st.session_state.transcript_text)
    st.session_state.extraction_result = extraction
    st.session_state.issue_text = extraction.issue_text
    st.session_state.response_text = extraction.response_text
    st.session_state.result = None
    st.session_state.email_draft = None
    st.session_state.transcript_status = extraction.reason


def save_current_review():
    result = st.session_state.result
    case_id = save_reviewed_case(
        CASE_DB_PATH,
        {
            "transcript_text": st.session_state.transcript_text,
            "issue_text": st.session_state.issue_text,
            "response_text": st.session_state.response_text,
            "recommended_category": result.recommended_category if result else "",
            "final_category": st.session_state.final_category,
            "responsible_owner": st.session_state.responsible_owner,
            "review_status": "reviewed",
            "reviewer": st.session_state.reviewer,
            "internal_note": st.session_state.internal_note,
        },
    )
    st.session_state.review_save_status = f"리뷰 완료 건 #{case_id}로 저장했습니다."


def generate_current_email_draft():
    st.session_state.email_draft = build_email_draft(
        issue_text=st.session_state.issue_text,
        response_text=st.session_state.response_text,
        category=st.session_state.final_category,
        responsible_owner=st.session_state.responsible_owner,
        owner_email="",
    )


def classify_current_text():
    result = classify_issue_response(
        st.session_state.issue_text,
        st.session_state.response_text,
        categories_path=CATEGORIES_PATH,
    )
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    matched_keywords = ", ".join(result.matched_keywords)
    st.session_state.result = result
    st.session_state.final_category = result.recommended_category
    history_row = {
        "time": created_at,
        "issue": st.session_state.issue_text,
        "response": st.session_state.response_text,
        "recommended_category": result.recommended_category,
        "final_category": result.recommended_category,
        "confidence": result.confidence,
        "needs_human_review": result.needs_human_review,
    }
    st.session_state.history.insert(0, history_row)
    st.session_state.history = st.session_state.history[:20]
    append_classification_result(
        RESULTS_CSV_PATH,
        {
            "created_at": created_at,
            "issue": history_row["issue"],
            "response": history_row["response"],
            "recommended_category": history_row["recommended_category"],
            "final_category": history_row["final_category"],
            "confidence": history_row["confidence"],
            "needs_human_review": history_row["needs_human_review"],
            "matched_keywords": matched_keywords,
        },
    )


def update_latest_final_category():
    if st.session_state.history:
        st.session_state.history[0]["final_category"] = st.session_state.final_category
        update_latest_csv_category(RESULTS_CSV_PATH, st.session_state.final_category)


def render_header(samples_count):
    st.markdown(
        f"""
        <div class="console-header">
          <div>
            <div class="eyebrow">CS CATEGORY AGENT · MVP</div>
            <div class="console-title">CS 이슈/대응 카테고리 자동 분류 Agent</div>
            <p class="console-subtitle">
              상담 기록의 이슈와 대응을 입력하면 규칙 기반 Agent가 추천 카테고리,
              신뢰도, 검토 필요 여부와 근거 키워드를 정리합니다.
            </p>
          </div>
          <div class="mode-pill">Synthetic data · {samples_count} samples</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_panel(samples):
    st.markdown(
        """
        <div class="section-title">
          <h3>상담 내용 입력</h3>
          <span>Issue & response workbench</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="planned-box">
          시험판은 비용이 들지 않도록 샘플 전사문 또는 직접 입력 전사문으로 전체 업무 흐름을 검증합니다.
          녹음본 STT는 향후 무료 로컬 모델을 기본 후보로 붙입니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("전사문 입력 및 이슈/대응 추출", expanded=True):
        st.text_area(
            "전사문",
            key="transcript_text",
            height=150,
            placeholder="예: 고객: 앱 업로드가 멈춰요. 상담사: 앱 재실행과 네트워크 확인을 안내했습니다.",
        )
        transcript_left, transcript_right = st.columns([1.2, 1])
        with transcript_left:
            st.button(
                "전사문에서 이슈/대응 추출",
                on_click=extract_current_transcript,
                disabled=not st.session_state.transcript_text.strip(),
                width="stretch",
            )
        with transcript_right:
            st.button("샘플 전사문 넣기", on_click=apply_demo_transcript, width="stretch")
        if st.session_state.transcript_status:
            st.caption(st.session_state.transcript_status)

    st.text_area("이슈", key="issue_text", height=190, placeholder="고객이 문의한 핵심 이슈를 입력하세요.")
    st.text_area("대응", key="response_text", height=150, placeholder="상담사 또는 내부 담당자의 대응 내용을 입력하세요.")

    st.caption("가상 상담 샘플")
    sample_columns = st.columns(3)
    for index, case in enumerate(samples[:5]):
        with sample_columns[index % 3]:
            st.button(
                case["title"][:18],
                key=f"sample_{index}",
                on_click=apply_sample,
                args=(case,),
                width="stretch",
            )

    action_left, action_right = st.columns([1.4, 1])
    with action_left:
        st.button(
            "카테고리 분류하기",
            type="primary",
            on_click=classify_current_text,
            width="stretch",
        )
    with action_right:
        st.button("초기화", on_click=clear_inputs, width="stretch")


def render_result(category_names):
    result = st.session_state.result
    st.markdown(
        """
        <div class="section-title">
          <h3>추천 결과</h3>
          <span>Agent decision</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result is None:
        st.markdown(
            """
            <div class="empty-state">
              분류 결과가 여기에 표시됩니다.<br>
              이슈와 대응을 입력한 뒤 버튼을 눌러주세요.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    review_class = "warn" if result.needs_human_review else "good"
    review_label = "사람 검토 필요" if result.needs_human_review else "자동 분류 가능"
    keyword_text = ", ".join(result.matched_keywords) if result.matched_keywords else "없음"

    st.markdown(
        f"""
        <div class="result-hero">
          <div class="result-label">추천 카테고리</div>
          <div class="result-category">{result.recommended_category}</div>
          <div class="badge-row">
            <span class="badge info">신뢰도 {result.confidence:.2f}</span>
            <span class="badge {review_class}">{review_label}</span>
          </div>
          <div class="result-label">매칭된 키워드</div>
          <div>{keyword_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="result-label">분류 사유</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="reason-box">{result.reason}</div>', unsafe_allow_html=True)

    default_index = category_names.index(result.recommended_category)
    st.selectbox(
        "최종 카테고리",
        category_names,
        index=default_index,
        key="final_category",
    )
    st.button("최종 카테고리 반영", on_click=update_latest_final_category, width="stretch")

    st.text_input("책임 주체", key="responsible_owner", placeholder="예: 앱 담당, 웹 담당, EB팀")
    st.text_input("리뷰어", key="reviewer", placeholder="예: CS 담당자")
    st.text_area("내부 메모", key="internal_note", height=90)

    review_left, review_right = st.columns(2)
    with review_left:
        st.button("리뷰 완료 저장", on_click=save_current_review, width="stretch")
    with review_right:
        st.button("메일 초안 생성", on_click=generate_current_email_draft, width="stretch")

    if st.session_state.review_save_status:
        st.caption(st.session_state.review_save_status)

    if st.session_state.email_draft:
        draft = st.session_state.email_draft
        st.text_input("메일 수신자", value=draft.to_email, disabled=True)
        st.text_input("메일 제목", value=draft.subject, disabled=True)
        st.text_area("메일 본문", value=draft.body, height=220)
        if draft.needs_recipient_review:
            st.caption("수신자 메일이 비어 있어 발송 전 담당자 확인이 필요합니다.")


def render_history():
    reviewed_cases = list_reviewed_cases(CASE_DB_PATH)
    st.markdown(
        """
        <div class="history-title">
          <div>
            <h3 style="margin:0;">리뷰 완료 기록</h3>
            <div class="small-note">CS 담당자가 확인한 최종 결과를 앱 안에 저장합니다.</div>
            <div class="small-note">리뷰 완료 저장소: data/reviewed_cases.db</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if reviewed_cases:
        reviewed_frame = pd.DataFrame(reviewed_cases)
        visible_review_columns = [
            "created_at",
            "issue_text",
            "response_text",
            "final_category",
            "responsible_owner",
            "reviewer",
            "internal_note",
        ]
        st.dataframe(reviewed_frame[visible_review_columns], width="stretch", hide_index=True)
    else:
        st.markdown(
            """
            <div class="empty-state" style="margin-top:12px;">
              아직 리뷰 완료로 저장된 기록이 없습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### 이번 세션 분류 결과")
    if not st.session_state.history:
        st.markdown(
            """
            <div class="empty-state" style="margin-top:12px;">
              아직 분류 결과가 없습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    frame = pd.DataFrame(st.session_state.history)
    visible_columns = [
        "time",
        "issue",
        "response",
        "recommended_category",
        "final_category",
        "confidence",
        "needs_human_review",
    ]
    st.dataframe(frame[visible_columns], width="stretch", hide_index=True)

    csv = frame.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSV 다운로드",
        data=csv,
        file_name="cs_category_results.csv",
        mime="text/csv",
    )


def main():
    st.set_page_config(
        page_title="CS 이슈/대응 카테고리 자동 분류 Agent",
        page_icon="CS",
        layout="wide",
    )
    init_state()
    load_styles()

    samples = cached_samples()
    category_names = cached_category_names()

    render_header(len(samples))

    metrics = st.columns(3)
    metrics[0].metric("카테고리 정의", f"{len(category_names)}개")
    metrics[1].metric("최근 분류", f"{len(st.session_state.history)}건")
    metrics[2].metric("데이터 모드", "가상 샘플")

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        with st.container(border=False):
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            render_input_panel(samples)
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        with st.container(border=False):
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            render_result(category_names)
            st.markdown("</div>", unsafe_allow_html=True)

    render_history()


if __name__ == "__main__":
    main()
