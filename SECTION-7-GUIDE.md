# 섹션 ⑦ Key Account 관리 구현 가이드

## 개요

편경현 고객사(섹션 ⑥)에서 선택한 "Key Account"를 별도의 섹션 ⑦에서 상세히 관리합니다.

**기능**:
- 섹션 ⑥에서 고객사별 "Key Account" 체크박스로 선택
- 선택된 고객사 정보를 섹션 ⑦에 실시간 표시
- 매출, 제품, 연락처 등 상세 정보 조회
- Capital/CDx별 Key Account 구분

---

## 1단계: 섹션 ⑥ HTML 수정

### 1-1. 테이블 헤더 추가

**파일**: `dashboard-original.html`  
**위치**: 라인 595-602

**변경 전**:
```html
<tr>
  <th style="text-align:left;min-width:50px">구분</th>
  <th style="text-align:left;min-width:140px">EndUser Address 1</th>
  <th style="text-align:left;min-width:160px">EndUser Customer Name 2</th>
  <th style="min-width:100px">YTD Net Sales</th>
  <th style="min-width:60px">제품수</th>
  <th style="min-width:50px">상세</th>
</tr>
```

**변경 후**:
```html
<tr>
  <th style="text-align:left;min-width:50px">구분</th>
  <th style="text-align:left;min-width:100px">고객세그먼트</th>
  <th style="text-align:left;min-width:140px">EndUser Address 1</th>
  <th style="text-align:left;min-width:160px">EndUser Customer Name 2</th>
  <th style="min-width:100px">YTD Net Sales</th>
  <th style="min-width:60px">제품수</th>
  <th style="min-width:50px">Key Account</th>
  <th style="min-width:50px">상세</th>
</tr>
```

---

## 2단계: 섹션 ⑥ JavaScript 수정

### 2-1. 테이블 렌더링 함수 수정

**파일**: `dashboard-original.html`  
**위치**: 라인 2366~2400 (섹션 ⑥ JS 영역)

다음 함수를 찾아서 수정하세요:

```javascript
// 기존 코드 (찾기)
function renderPyunTable() {
  const clients = currentFilter === 'cap' ? PYUN.cap_clients : PYUN.cdx_clients;
  if (!clients || clients.length === 0) return;
  
  const tbody = document.getElementById('pyunTbody');
  tbody.innerHTML = clients.map((c, i) => `
    <tr>
      <td>${c.category}</td>
      <td>${c.addr}</td>
      <td onclick="showPyunDetail(${i},'${currentFilter}')" style="cursor:pointer;color:#0057A8">${c.name}</td>
      <td style="text-align:right">${(c.total_sales).toLocaleString('ko-KR')}</td>
      <td style="text-align:center">${c.product_count}</td>
      <td><button onclick="showPyunDetail(${i},'${currentFilter}')">상세</button></td>
    </tr>
  `).join('');
}

// 수정 코드 (변경)
function renderPyunTable() {
  const clients = currentFilter === 'cap' ? PYUN.cap_clients : PYUN.cdx_clients;
  if (!clients || clients.length === 0) return;
  
  const tbody = document.getElementById('pyunTbody');
  tbody.innerHTML = clients.map((c, i) => `
    <tr>
      <td>${c.category}</td>
      <td>${c.segment || '일반'}</td>
      <td>${c.addr}</td>
      <td onclick="showPyunDetail(${i},'${currentFilter}')" style="cursor:pointer;color:#0057A8">${c.name}</td>
      <td style="text-align:right">${(c.total_sales).toLocaleString('ko-KR')}</td>
      <td style="text-align:center">${c.product_count}</td>
      <td style="text-align:center">
        <input type="checkbox" 
               ${c.is_key_account ? 'checked' : ''} 
               onchange="toggleKeyAccount(${i},'${currentFilter}')"
               style="cursor:pointer">
      </td>
      <td><button onclick="showPyunDetail(${i},'${currentFilter}')">상세</button></td>
    </tr>
  `).join('');
}
```

### 2-2. Key Account 토글 함수 추가

라인 2366 근처에 다음 함수를 추가하세요:

```javascript
// Key Account 선택/해제
function toggleKeyAccount(idx, filter) {
  const clients = filter === 'cap' ? PYUN.cap_clients : PYUN.cdx_clients;
  clients[idx].is_key_account = !clients[idx].is_key_account;
  
  // 섹션 ⑦ 업데이트
  renderKeyAccountSection();
}

// Key Account 섹션 렌더링
function renderKeyAccountSection() {
  const keyAccounts = [];
  
  // Capital Key Accounts 수집
  PYUN.cap_clients.forEach(c => {
    if (c.is_key_account) {
      keyAccounts.push({...c, type: 'Capital'});
    }
  });
  
  // CDx Key Accounts 수집
  PYUN.cdx_clients.forEach(c => {
    if (c.is_key_account) {
      keyAccounts.push({...c, type: 'CDx'});
    }
  });
  
  // 매출액 기준 정렬
  keyAccounts.sort((a, b) => b.total_sales - a.total_sales);
  
  // 섹션 ⑦ 콘텐츠 생성
  const container = document.getElementById('s7');
  if (!container) return;
  
  const kpiHtml = generateKeyAccountKPI(keyAccounts);
  const tableHtml = generateKeyAccountTable(keyAccounts);
  
  container.querySelector('.section').innerHTML = `
    <div class="sec-hd">
      <div class="sec-badge" style="background:#fff3e0;color:#e65100">⑦</div>
      <div class="sec-title">Key Account 관리</div>
      <div class="sec-note">선택된 고객사 상세 정보 | 담당자: Kyung-Hyun Pyun</div>
    </div>
    
    ${kpiHtml}
    ${tableHtml}
  `;
}

// Key Account KPI 생성
function generateKeyAccountKPI(keyAccounts) {
  if (keyAccounts.length === 0) {
    return `<div style="padding:20px;text-align:center;color:#999">
              Key Account를 선택해주세요 (섹션 ⑥에서 체크박스 클릭)
            </div>`;
  }
  
  const totalSales = keyAccounts.reduce((sum, c) => sum + c.total_sales, 0);
  const capitalCount = keyAccounts.filter(c => c.type === 'Capital').length;
  const cdxCount = keyAccounts.filter(c => c.type === 'CDx').length;
  
  return `
    <div class="kpi-row" style="margin-bottom:16px">
      <div class="kpi" style="border-color:#e65100;background:rgba(230, 90, 0, 0.04)">
        <div class="kpi-label">선택된 Key Account</div>
        <div class="kpi-grid">
          <div class="kpi-cell">
            <span class="kc-lbl">총 고객사</span>
            <span class="kc-val">${keyAccounts.length}<span class="kc-unit">개</span></span>
          </div>
          <div class="kpi-cell">
            <span class="kc-lbl">Capital</span>
            <span class="kc-val">${capitalCount}<span class="kc-unit">개</span></span>
          </div>
          <div class="kpi-cell">
            <span class="kc-lbl">CDx</span>
            <span class="kc-val">${cdxCount}<span class="kc-unit">개</span></span>
          </div>
        </div>
      </div>
      <div class="kpi" style="border-color:#e65100;background:rgba(230, 90, 0, 0.04)">
        <div class="kpi-label">YTD 누적 매출</div>
        <div class="kpi-grid">
          <div class="kpi-cell">
            <span class="kc-lbl">총 매출액</span>
            <span class="kc-val" style="color:#e65100;font-size:20px;font-weight:bold">
              ${(totalSales).toLocaleString('ko-KR')}<span class="kc-unit" style="font-size:12px">원</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  `;
}

// Key Account 테이블 생성
function generateKeyAccountTable(keyAccounts) {
  if (keyAccounts.length === 0) {
    return '';
  }
  
  const tableRows = keyAccounts.map(c => `
    <tr>
      <td>${c.type}</td>
      <td>${c.segment || '일반'}</td>
      <td>${c.addr}</td>
      <td style="cursor:pointer;color:#0057A8">${c.name}</td>
      <td style="text-align:right;font-weight:bold">${(c.total_sales).toLocaleString('ko-KR')}</td>
      <td style="text-align:center">${c.product_count}</td>
      <td style="text-align:center">
        <a href="javascript:void(0)" onclick="showKeyAccountProducts('${c.name}')" 
           style="color:#0057A8;text-decoration:none">
          [제품]
        </a>
        ${c.contacts && c.contacts.length > 0 ? `
          <a href="javascript:void(0)" onclick="showKeyAccountContacts('${c.name}')" 
             style="color:#0057A8;text-decoration:none;margin-left:4px">
            [연락처]
          </a>
        ` : ''}
      </td>
    </tr>
  `).join('');
  
  return `
    <div class="ct-card">
      <div class="ct-title">Key Account 고객사 목록 (2026 YTD, 단위: 원)</div>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead>
          <tr>
            <th style="min-width:50px">구분</th>
            <th style="min-width:100px">세그먼트</th>
            <th style="min-width:140px">주소</th>
            <th style="min-width:160px">고객사명</th>
            <th style="min-width:100px">YTD 매출</th>
            <th style="min-width:50px">제품수</th>
            <th style="min-width:80px">상세</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
      </div>
    </div>
  `;
}

// Key Account 제품 상세 표시
function showKeyAccountProducts(customerName) {
  const allClients = [...PYUN.cap_clients, ...PYUN.cdx_clients];
  const client = allClients.find(c => c.name === customerName);
  
  if (!client || !client.products) {
    alert('제품 정보가 없습니다.');
    return;
  }
  
  const html = `
    <h3>${client.name} - 상위 10개 제품</h3>
    <table class="data-table" style="width:100%;margin-top:12px">
      <thead>
        <tr>
          <th>Product Number</th>
          <th>Product Name</th>
          <th>Sales (원)</th>
        </tr>
      </thead>
      <tbody>
        ${client.products.map(p => `
          <tr>
            <td>${p.pn}</td>
            <td>${p.pname}</td>
            <td style="text-align:right">${(p.sales).toLocaleString('ko-KR')}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  alert(html); // 또는 모달로 표시
}

// Key Account 연락처 표시
function showKeyAccountContacts(customerName) {
  const allClients = [...PYUN.cap_clients, ...PYUN.cdx_clients];
  const client = allClients.find(c => c.name === customerName);
  
  if (!client || !client.contacts || client.contacts.length === 0) {
    alert('연락처 정보가 없습니다.');
    return;
  }
  
  const html = `
    <h3>${client.name} - 연락처</h3>
    <table class="data-table" style="width:100%;margin-top:12px">
      <thead>
        <tr>
          <th>이름</th>
          <th>직책</th>
          <th>이메일</th>
          <th>연락처</th>
        </tr>
      </thead>
      <tbody>
        ${client.contacts.map(c => `
          <tr>
            <td>${c.name || '-'}</td>
            <td>${c.department || '-'}</td>
            <td><a href="mailto:${c.email}">${c.email || '-'}</a></td>
            <td>${c.phone || '-'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  alert(html); // 또는 모달로 표시
}
```

---

## 3단계: 섹션 ⑦ HTML 추가

### 3-1. 탭 버튼 추가

**위치**: 라인 232 (탭 바 영역)

**변경 전**:
```html
<button class="hero-tab" onclick="showSec('s6',this)" style="border-left:1px solid rgba(255,255,255,0.1)">⑥ 편경현 고객사</button>
```

**변경 후**:
```html
<button class="hero-tab" onclick="showSec('s6',this)" style="border-left:1px solid rgba(255,255,255,0.1)">⑥ 편경현 고객사</button>
<button class="hero-tab" onclick="showSec('s7',this)">⑦ Key Account</button>
```

### 3-2. 섹션 ⑦ 컨테이너 추가

**위치**: 라인 636 (섹션 ⑥ 닫은 후)

**추가할 코드**:
```html
<!-- SECTION 7: Key Account 관리 -->
<div id="s7" class="container" style="display:none">
  <div class="section">
    <!-- 내용은 JavaScript에서 동적으로 생성됨 -->
  </div>
</div><!-- /s7 -->
```

---

## 4단계: 초기화 함수 호출

### 4-1. init() 함수 끝에 추가

**위치**: 라인 2400 이후 (초기화 함수 영역)

```javascript
function init() {
  // 기존 코드들...
  
  // 섹션 ⑦ 초기화
  renderKeyAccountSection();
}
```

---

## 5단계: CSS 스타일 추가 (선택사항)

```css
/* Key Account 스타일 */
.key-account-highlight {
  background: rgba(230, 90, 0, 0.05);
  border-left: 4px solid #e65100;
}

.key-account-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
```

---

## 테스트 체크리스트

- [ ] 섹션 ⑥에서 체크박스가 표시되는가?
- [ ] 체크박스를 클릭하면 섹션 ⑦에 고객사가 추가되는가?
- [ ] 체크박스를 해제하면 섹션 ⑦에서 제거되는가?
- [ ] Key Account KPI가 올바르게 계산되는가?
- [ ] [제품] 링크가 작동하는가?
- [ ] [연락처] 링크가 작동하는가? (Contacts.xlsx 추출 필요)

---

## 예상 결과

**섹션 ⑥**:
```
구분 | 고객세그먼트 | EndUser Address | EndUser Customer Name | 매출 | 제품수 | Key Account (체크박스) | 상세
```

**섹션 ⑦**:
```
⑦ Key Account 관리

KPI: 선택된 고객사 5개 (Capital 3, CDx 2) | YTD 총매출: 1,234,567,890원

고객사 목록 (매출액 내림차순)
- 삼성바이오에피스     491,895,070원  [제품] [연락처]
- 종근당 효종연구소    322,975,110원  [제품] [연락처]
- ...
```

---

## 추가 고려사항

### 데이터 저장
현재는 메모리에만 저장됩니다. 필요시 localStorage에 저장:

```javascript
function saveKeyAccounts() {
  const keyAccounts = {
    cap: PYUN.cap_clients.filter(c => c.is_key_account).map(c => c.name),
    cdx: PYUN.cdx_clients.filter(c => c.is_key_account).map(c => c.name)
  };
  localStorage.setItem('keyAccounts', JSON.stringify(keyAccounts));
}

function loadKeyAccounts() {
  const saved = localStorage.getItem('keyAccounts');
  if (!saved) return;
  
  const keyAccounts = JSON.parse(saved);
  keyAccounts.cap.forEach(name => {
    const client = PYUN.cap_clients.find(c => c.name === name);
    if (client) client.is_key_account = true;
  });
  keyAccounts.cdx.forEach(name => {
    const client = PYUN.cdx_clients.find(c => c.name === name);
    if (client) client.is_key_account = true;
  });
}
```

---

## 참고: 키 파일

- 원본 대시보드: `dashboard-original.html`
- 데이터 추출 스크립트: `update_dashboard.py`
- 이 가이드: `SECTION-7-GUIDE.md`
