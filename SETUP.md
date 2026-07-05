# PK Sales Dashboard 월별 업데이트 가이드

## 개요

이 대시보드는 Promega Korea의 매출/영업 현황을 모니터링하는 단일 HTML 파일입니다.  
모든 데이터는 HTML 내 JavaScript 객체로 임베딩되어 있으며, 서버 없이 로컬 브라우저에서 실행됩니다.

**주 사용자**: 편경현 (Kyung Hyun Pyun)  
**업데이트 주기**: 월별 (데이터 확정 후)

---

## 파일 구조

```
dashboard-original.html     대시보드 HTML 파일 (412KB)
├── Chart.js 4.4.1         차트 렌더링 라이브러리 (인라인 번들)
├── const D = {...}        사업부 매출 데이터 (라인 725)
├── const PYUN = {...}     편경현 고객사 데이터 (라인 2368)
└── 렌더링 함수들

update_dashboard.py        월별 자동화 스크립트
├── DashboardUpdater       HTML 데이터 객체 업데이트
├── ExcelDataExtractor     Excel 파일에서 데이터 추출
└── 실행 함수들

index.html                 (현재는 테스트용 템플릿)
```

---

## 데이터 구조

### const D (사업부 매출)

```javascript
const D = {
  div: {
    "Capital": { gr_ann: 0.12, 시약: {...}, 장비: {...}, 합계: {...} },
    "Strategic CDx": { ... },
    "Local": { ... },
    "Strategic Forensic": { ... }
  },
  grand: { 시약: {...}, 장비: {...}, 합계: {...} },
  secs: [ /* 섹션 구조 */ ],
  chs: [ /* 채널별 데이터 */ ]
};
```

**필드 설명**:
| 필드 | 의미 | 예시 |
|------|------|------|
| ta | 연간 Target | 14,560,609,000 |
| ga | 연간 성장률 목표 | 0.124722 (12.47%) |
| tgt | 당월 Target | 1,310,400,000 |
| act | 당월 실적 | 1,258,178,492 |
| ac | 당월 달성률 | 0.960148 (96%) |
| ytd | YTD 누적 실적 | 6,736,686,044 |
| ay | YTD 달성률 | 0.970498 (97%) |
| aa | 연간 달성률 | 0.462665 (46.3%) |
| gr | YTD 성장률 | 0.178258 (17.8%) |
| gm | 당월 성장률 | 0.137806 (13.8%) |

### const PYUN (편경현 고객사)

```javascript
const PYUN = {
  cap_total: 2,502,303,554,        // Capital 총 매출
  cdx_total: 430,060,274,          // CDx 총 매출
  grand_total: 2,932,363,828,      // 합계
  cap_count: 107,                  // Capital 고객사 수
  cdx_count: 34,                   // CDx 고객사 수
  cap_clients: [
    {
      addr: "삼성바이오에피스",
      name: "삼성바이오에피스",
      category: "Capital",
      total_sales: 491,895,070,
      product_count: 17,
      products: [
        { pn: "V1711", pname: "CellTiter-Glo...", sales: 123456789 },
        ...
      ]
    },
    ...
  ],
  cdx_clients: [ /* 동일 구조 */ ]
};
```

---

## 월별 업데이트 절차

### 1단계: 데이터 준비

OnDrive에서 다음 파일을 **저장소에 복사**합니다:

```
📁 OnDrive 경로:
├── 스캔\세일즈\Reporter Foldr\4) Target\2. Target\
│   └── 8. 2026' Target(CUSD 1,300원)_v6.xlsx      → 저장소: Target.xlsx
├── 판매 내역\BOBJ_ZEUC\
│   └── 4. 판매 내역(25~26년)_6월_H2담당자.xlsx   → 저장소: Sales.xlsx
└── 스캔\세일즈\90 Day project\
    └── 2. All active contact info. 26년 6월.xlsx → 저장소: Contacts.xlsx
```

**주의**: 
- 판매 내역 파일은 피벗 테이블을 포함하고 있어 MS Graph 추출 불가
- 로컬에 복사해서 Python pandas로 처리해야 함

### 2단계: 자동화 스크립트 실행

```bash
# 저장소 디렉토리에서:
python3 update_dashboard.py \
  --target Target.xlsx \
  --sales Sales.xlsx \
  --output index.html \
  --month 6 \
  --year 2026
```

**옵션 설명**:
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| --target | Target Excel 파일 경로 | Target.xlsx |
| --sales | 판매 내역 Excel 파일 경로 | Sales.xlsx |
| --output | 출력 HTML 파일 | index.html |
| --month | 보고월 (1-12) | 현재 월 |
| --year | 보고년 | 2026 |

### 3단계: 검증

```bash
# HTML 파일 열기 (브라우저)
open index.html

# 또는
firefox index.html

# 또는
google-chrome index.html
```

### 4단계: Git에 커밋 및 푸시

```bash
git add index.html
git commit -m "feat: Update dashboard with June data (2026-07-05)"
git push origin claude/pk-sales-dashboard-ih9nhd
```

---

## 전제 조건

### 시스템 요구사항
- Python 3.7+
- 필수 패키지:
  ```bash
  pip install pandas openpyxl
  ```

### 파일 요구사항

#### Target Excel (필수)
- **파일명 패턴**: `*2026*Target*.xlsx`
- **필수 시트**: Capital, CDx, Local, Forensic 등 사업부별 시트
- **필수 컬럼** (자동 감지):
  - 연간 Target (Annual Target)
  - 당월 Target/실적
  - YTD 누적
  - 성장률

#### 판매 내역 Excel (필수, PYUN 섹션용)
- **필수 시트**: 매출 내역 또는 첫 번째 시트
- **필수 컬럼** (자동 감지):
  - 담당자 / Owner (필터용)
  - 고객명 (EndUser Customer Name)
  - 제품번호 (Product Number)
  - 제품명 (Product Name)
  - 매출액 (Net Sales)
  - 연도 (Year Name, "CY 2026" 필터)

#### 고객 연락처 Excel (선택, 향후 통합용)
- **필수 컬럼**:
  - Company Name (고객사명)
  - Contact Name
  - Email
  - Phone
  - Owner (담당자)

---

## 데이터 추출 로직

### const D 추출 프로세스

1. **시트 인식**: Capital, CDx, Local, Forensic 자동 감지
2. **컬럼 매핑**: 연간목표, 당월목표/실적 등 자동 감지
3. **계산**:
   - 달성률 = 실적 ÷ 목표
   - YTD 성장률 = (올해 실적 - 작년 같은기간) ÷ 작년 같은기간
   - 연간 달성률 = YTD 실적 ÷ 연간 Target
4. **JSON 생성**: const D 객체 형태로 JSON 변환

### const PYUN 추출 프로세스

1. **필터링**: 
   - Owner = "Kyung-Hyun Pyun" → Capital
   - Owner = "Kyung-Hyun Pyun_CDx" → CDx
   - Year = "CY 2026"
2. **그룹화**: 고객사별 매출 집계
3. **정렬**: 매출액 내림차순
4. **상위 상품**: 고객당 상위 10개 제품 추출
5. **JSON 생성**: const PYUN 객체 형태로 JSON 변환

---

## 알려진 제약 및 한계

| 항목 | 설명 | 해결책 |
|------|------|--------|
| Excel 피벗 포함 | MS Graph 추출 불가 | 파일을 저장소에 복사 후 pandas 사용 |
| 자동 갱신 미지원 | 수동 업데이트만 가능 | 매달 스크립트 실행 필요 |
| 파일 크기 큼 | dashboard.html ~410KB | Chart.js 인라인 번들, 최적화 여지 있음 |
| 연락처 미통합 | 섹션 ⑥에 CRM 매칭 불완료 | 향후 업데이트 예정 |

---

## 향후 개선 계획

### 1단계: 자동화 강화 (우선순위: 높음)
- [ ] Excel 컬럼명 설정 파일화 (config.json)
- [ ] 월별 파일 자동 감지
- [ ] 에러 복구 로직 개선
- [ ] 단위 테스트 추가

### 2단계: 데이터 통합 (우선순위: 중간)
- [ ] 고객 연락처 매칭 (섹션 ⑥ 강화)
- [ ] CRM 이메일 히스토리 추출
- [ ] Teams 채팅 기록 검색

### 3단계: 시각화 개선 (우선순위: 낮음)
- [ ] 대시보드 반응형 디자인 강화
- [ ] 모바일 최적화
- [ ] 내보내기 기능 (PDF, Excel)

---

## FAQ

**Q. Excel 파일을 OnDrive에서 저장소로 어떻게 가져오나요?**

A. 현재 다음 방법들을 사용할 수 있습니다:
1. OneDrive 동기화 폴더에서 직접 복사
2. 웹 OnDrive에서 다운로드
3. GitHub에 업로드 (CLI 또는 웹)

**Q. 스크립트가 Excel을 못 읽으면?**

A. 다음을 확인하세요:
1. 파일 형식이 .xlsx인지 확인 (구 Excel .xls는 지원 안 함)
2. 파일이 손상되지 않았는지 확인
3. 필수 컬럼이 있는지 확인
4. 스크립트 디버그 출력 확인

**Q. const D와 const PYUN을 수동으로 수정할 수 있나요?**

A. 네, 가능합니다:
1. dashboard.html을 텍스트 편집기로 열기
2. 라인 725 (const D) 또는 2368 (const PYUN) 찾기
3. JSON 객체 수정 (문법 실수 주의)
4. 저장 후 브라우저 새로고침

---

## 지원 및 문의

- **개발자**: Claude Code (Anthropic)
- **세션**: https://claude.ai/code/session_018vsBbuU21XTbRSDQ1cvG2U
- **저장소**: https://github.com/kpyun/1.-Promega_Sales_Dashboard_2026_6-Fcst
