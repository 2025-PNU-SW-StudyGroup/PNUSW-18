# 🤖 은행 내부 직원 전용 금융 비서 AI 챗봇

> 본 프로젝트는 은행 직원들이 보다 효율적으로 고객을 응대하고 금융상품 관련 질의를 처리할 수 있도록 AI 챗봇을 개발하는 것을 목표로 합니다. 영업직 은행원은 다양한 금융상품과 내부 프로세스를 숙지해야 하지만, 모든 정보를 외우거나 빠르게 찾는 데 어려움을 겪을 수 있습니다. 현재 은행 내 챗봇은 키워드 검색 방식으로 운영되며, 연관된 모든 정보를 나열하는 방식이라 가독성이 떨어지고 원하는 정보를 정확하게 찾기 어렵다는 한계가 있습니다. 이에 따라 맥락을 이해하고 핵심 정보를 간결하게 제공할 수 있는 AI 챗봇을 개발하여 직원들의 정보 탐색 부담을 줄이고 업무 효율성을 높이고자 합니다.

### 1. 프로젝트 소개

#### 1.1. 개발배경 및 필요성

은행 영업직은 은행 내 보유하고 있는 수많은 금융상품(예금, 대출, 카드 등) 정보를 실시간으로 고객에게 제공해야 하는 대면업무를 맡고 있습니다. 그러나 금융상품의 방대한 내용과 매뉴얼, 그리고 변화하는 은행 내 금융지침 또는 국가정책으로 인해 모든 상품의 세부 정보를 숙지하는 것은 현실적으로 어렵습니다. 또한, 현재 은행은 일반 챗봇을 운용하고 있으나 이는 키워드 기반 검색으로 정확한 검색어가 필요하여 사실상 업무 초기의 직원은 능숙하게 사용하기 쉽지 않습니다. 검색을 했다 하더라도 모든 정보 및 매뉴얼이 핵심 정보 위주로 요약되지 않고, 원문을 그대로 나열하는 형식으로 응답하기 때문에 짧은 시간 내에 고객과 소통해야 하는 영업업무에서 적합하지 않습니다. 따라서 저희 팀은 해당 문제점을 보완하여 은행 내부 직원이 실질적으로 능률을 높일 수 있는 AI 챗봇을 만들고자 합니다.

#### 1.2. 개발 목표 및 주요 내용

본 프로젝트의 목표는 은행 내부 직원이 빠르고 정확하게 금융상품 세부 정보를 조회할 수 있도록 돕는 AI 챗봇을 개발하는 것입니다. 단순 키워드 검색 방식에서 발생하는 어려움을 해소하기 위해 질문의 전체 맥락을 이해하고 간결하게 요약된 정보를 제공하는 챗봇을 개발하여, 궁극적으로는 행원의 업무 효율성을 극대화하고 고객 응대 서비스의 품질을 향상시키고자 합니다.

본 프로젝트의 주요 기능은 총 세 가지로 정리될 수 있습니다. 첫째, 맥락 기반의 금융상품 검색 및 조회 기능입니다. 은행 직원이 금융상품(주로 여수신)의 자격요건, 필요서류, 마감기한, 금리 변동 등을 모두 숙지하고 있기 어렵기에 이에 관한 세부 정보를 요청하였을 때 정보를 요약하여 제공할 수 있습니다. 이때 정확한 키워드를 사용하여 질문하지 않아도 질문 전체의 맥락을 고려하여 AI 기능을 통해 핵심 정보를 유추하고 제공합니다. 둘째, FAQ 자동 응답 기능입니다. 은행 직원이 자주 묻는 질문을 AI 기능을 통해 학습하여 보다 빠르고 정확한 답변을 제공할 수 있습니다. 이에 관해 전체 은행 직원이 사용하는 챗봇을 관리하는 관리자 페이지를 생성하여 운용할 수 있습니다. 셋째, 업데이트 자동 반영 기능입니다. 본래는 은행 내 기밀 정보를 가지고 답변하겠으나, 현실적으로 외부에서 얻을 수 있는 홈페이지 정보를 크롤링하여 답변 데이터를 쌓습니다. 목표는 1시간 주기로 정보를 업데이트하여 최신 금융상품 정보를 알 수 있도록 답변의 질을 개선해 나가고자 합니다.

본 프로젝트는 두 가지 기대효과를 가질 것으로 예상합니다. 첫째, 대면 업무 효율성이 향상될 것이라고 기대합니다. 은행 직원들은 필요한 세부 정보를 빠르고 간결한 답변을 통해 얻어낼 수 있습니다. 때문에 매뉴얼을 찾아나서는 시간이 급격히 단축되면서 업무 효율도를 증대시킬 수 있습니다. 둘째, 고객 만족도가 증가합니다. 업무 처리 속도가 증가하면서 고객은 보다 신속하게 고객에게 알맞은 금융상품을 안내 받을 수 있습니다. 따라서 고객지향적인 금융상품을 제공받아 높은 만족도를 가질 수 있습니다.

본 프로젝트는 은행 내 IT 기술 활용을 증진시키고, 실제 금융영업 업무에서 AI 기술의 실현가능성을 입증하는 것을 목표로 두고 있습니다.

#### 1.3. 세부내용

**요구사항 분석**

-  대상: KB국민은행 사내 직원(개인금융 담당)

-  주요 요구사항
   -  사내 직원을 대상으로 하는 Q&A 및 CS 업무 처리
   -  ChatGPT, Grok 등과 유사한 대화형 챗봇 인터페이스
   -  질문에 포함된 복잡한 검색 조건을 이해하는 능력
   -  검색 결과를 참고하여 질문에 대한 정확하고 명료한 답변 제공
   -  참고 자료에 대한 출처 표기(URL 형식)
   -  사용자별 개인화를 위한 다양한 기능(Custom Instruction 등)
   -  모니터링 및 계정 관리를 위한 관리자 대시보드
   -  모델 정확도 개선을 위한 채팅 내역 수집

**제한사항 및 대책**

-  내부망에서 외부 API 접근 제한

   실제로는 사내망에 GPU 서버를 직접 구축하고, 오픈소스 또는 오픈웨이트 모델도 직접 서빙해야 합니다. 하지만 프로토타입 단계에서 GPU 서버 구축 및 LLM 서빙까지 하는 것은 현실적인 제약이 많으므로, Text Embedding 및 Reranker 서버까지만 구축 후 시연 예정입니다.

-  범용 언어 모델의 한국어 및 금융 도메인에 대한 이해 부족

   미국, 중국의 언어 모델은 사전 학습(Pre-training) 단계에서 절대적인 한국어 데이터셋의 양이 부족한 경우가 많습니다. 더욱이 금융 분야와 같은 특정 도메인에 대한 한국어 데이터는 더더욱 부족합니다. 이를 보완하기 위해, 금융 분야 전반에 대한 한국어 데이터셋을 충분히 확보하여 Text Embedding, Reranker, LLM 등을 미세 조정(Fine-tuning)할 필요가 있습니다.

-  평가 데이터셋 부족

   챗봇의 성능 평가에 사용할 Evaluation 데이터셋을 구축하기가 까다롭습니다. 공개된 한국어 데이터셋이 있긴 하지만, 범용 데이터셋이기 때문에 우리 도메인에 적합한 데이터셋을 선별하고, 추가하는 작업이 필요합니다. 따라서 allganize사의 RAG-Evaluation-Dataset-KO를 참고 및 활용하여 자체 데이터셋을 구축 예정입니다.

#### 1.4. 기존 서비스 대비 차별성

본 프로젝트는 기존 서비스 대비 세 가지 차별성을 지닐 수 있습니다. 첫째, 맥락 이해 능력이 향상됩니다. 기존 챗봇은 키워드 중심 검색으로 정확한 키워드를 입력하지 않는다면 원하는 결과를 얻을 수 없습니다. 반면 본 프로젝트의 AI 챗봇은 질문의 의도를 맥락에 따라 파악하여 사용자가 원하는 핵심 정보만을 간결하게 답변할 수 있습니다. 둘째, 응답 구조의 가독성을 높입니다. 기존 챗봇은 핵심 정보만 요약되지 않고 관련 정보 전체를 나열하여 답변합니다. 반면 본 프로젝트의 AI 챗봇은 질문의 의도를 맥락에 따라 파악하여 가장 필요한 정보만 요약하여 간결하게 제공할 수 있습니다. 셋째, 업무 생산성이 향상될 수 있습니다. 기존 챗봇은 사용자가 방대한 양의 검색결과(전체 매뉴얼 등) 속에서 직접 정보를 찾아내야 했습니다. 반면 본 프로젝트의 AI 챗봇은 실시간으로 정보를 업데이트하고 자주 묻는 질문을 학습하는 등 AI 기능을 통해 빠르고 정확하게 필요한 정보를 제공할 수 있습니다.

#### 1.5. 사회적가치 도입 계획

> 위 내용을 작성하세요.

### 2. 상세설계

#### 2.1. 시스템 구성도

> 시스템 구성도(infra, front, back등의 node 간의 관계)의 사진을 삽입하세요.

#### 2.1. 사용 기술

-  DB: PostgreSQL (pgvector)
-  API Server: Python 3.12 (FastAPI, SQLAlchemy, Alembic)
-  Crawler: Python 3.12 (Selenium, BeautifulSoup, SQLAlchemy, Alembic)
-  Text Embedding: BAAI/bge-m3 기반의 파생 모델
-  Text Embedding Server: Python 3.10 (FastAPI, llama-cpp-python, onnxruntime-gpu)
-  Reranker: BAAI/bge-reranker-v2-m3
-  Reranker Server: Hugging Face Text Embedding Inference
-  Chat Completion: gpt-4o-mini(또는 gpt-4o)
-  Frontend, Web: React.js(TypeScript), Tailwind CSS, nginx
-  Deploy: AWS EC2 + ALB(API, Web), 홈서버(DB, Crawler, Text Embedding, Reranker)

### 3. 개발결과

#### 3.1. 전체시스템 흐름도

> 위 내용을 작성하세요.

#### 3.2. 기능설명

> 각 페이지 마다 사용자의 입력의 종류와 입력에 따른 결과 설명 및 시연 영상.
>
> ex. 로그인 페이지:
>
> -  이메일 주소와 비밀번호를 입력하면 입력창에서 유효성 검사가 진행됩니다.
> -  유효성 검사를 통과하지 못한 경우, 각 경고 문구가 입력창 하단에 표시됩니다.
> -  유효성 검사를 통과한 경우, 로그인 버튼이 활성화 됩니다.
> -  로그인 버튼을 클릭 시, 입력한 이메일 주소와 비밀번호에 대한 계정이 있는지 확인합니다.
> -  계정이 없는 경우, 경고문구가 나타납니다.
>
> (영상)

#### 3.3. 기능명세서

> 개발한 제품에 대한 기능명세서를 작성해 제출하세요.
>
> 노션 링크, 한글 문서, pdf 파일, 구글 스프레드 시트 등...

#### 3.4. 디렉토리 구조

> 위 레포지토리의 디렉토리 구조를 설명하세요.

### 4. 설치 및 사용 방법

> 제품을 설치하기 위헤 필요한 소프트웨어 및 설치 방법을 작성하세요.
>
> 제품을 설치하고 난 후, 실행 할 수 있는 방법을 작성하세요.

### 5. 소개 및 시연 영상

> 프로젝트에 대한 소개와 시연 영상을 넣으세요.
> 프로젝트 소개 동영상을 교육원 메일(swedu@pusan.ac.kr)로 제출 이후 센터에서 부여받은 youtube URL주소를 넣으세요.

### 6. 팀 소개

| **김예원** | **강민석** | **이지수** | **이채은** |
|:-:|:-:|:-:|:-:|
| <img src="https://github.com/rladPdnjs.png" width="100" height="100" style="border-radius: 50%;"> | <img src="https://github.com/myeolinmalchi.png" width="100" height="100" style="border-radius: 50%;"> | <img src="https://github.com/dlwltn0430.png" width="100" height="100" style="border-radius: 50%;"> | <img src="https://github.com/rladPdnjs.png" width="100" height="100" style="border-radius: 50%;">
| **팀장 / 디자이너** | **백엔드 개발** | **프론트엔드 개발** | **PM** |
| [Github](https://github.com/rladPdnjs) | [Github](https://github.com/myeolinmalchi) | [Github](https://github.com/dlwltn0430) | - |
| yewon1799@pusan.ac.kr | rkd2274@pusan.ac.kr | dlwltn0430@pusan.ac.kr | dlcodms49@naver.com |

### 7. 해커톤 참여 후기

> 팀원 별 해커톤 참여 후기를 작성하세요.
