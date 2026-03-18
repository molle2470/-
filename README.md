# Advanced Harness

Claude Code를 위한 고급 스킬/커맨드 모음 모노레포. FastAPI 백엔드 + Next.js 15 프론트엔드 프로젝트에 Claude Code 자동화 스킬, 프레임워크 가이드라인을 통합하여 개발 생산성을 극대화합니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.12, FastAPI, SQLModel, PostgreSQL, asyncpg |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS 4, MUI |
| **AI Agent** | Pydantic AI, SSE streaming |

## Skills (15개)

| # | 스킬 | 설명 |
|---|------|------|
| 4 | `fastapi-backend-guidelines` | FastAPI 백엔드 DDD 개발 가이드 - SQLModel ORM, 레포지토리 패턴, async/await |
| 6 | `mermaid` | Mermaid 다이어그램 생성 - 플로우차트, ER, 간트 등 23종 지원 |
| 7 | `nextjs-frontend-guidelines` | Next.js 15 프론트엔드 가이드 - App Router, shadcn/ui, Tailwind CSS 4, 한국어 로컬라이제이션 |
| 8 | `pdf` | PDF 읽기/병합/분할/회전/워터마크/생성/OCR 등 전방위 처리 |
| 10 | `pptx` | PowerPoint 생성/편집/분석 - HTML→PPTX 변환, OOXML 편집 |
| 13 | `vercel-react-best-practices` | Vercel 엔지니어링 기준 React/Next.js 성능 최적화 가이드 |
| 14 | `web-design-guidelines` | Vercel Web Interface Guidelines 기반 UI 코드 접근성/UX 리뷰 |

## Commands (3개)

| 커맨드 | 설명 |
|--------|------|
| `/dev-docs-update` | 컨텍스트 컴팩션 전 개발 문서(active task, 세션 상태) 업데이트 |
| `/dev-docs` | 전략적 개발 계획 생성 - `dev/active/`에 plan/context/tasks 구조화 |
| `/route-research-for-testing` | 편집된 라우트 자동 감지 후 auth-route-tester로 스모크 테스트 |

## Agents (12개)

자율적으로 복잡한 서브태스크를 수행하는 전문 에이전트입니다.

| # | 에이전트 | 설명 |
|---|---------|------|
| 8 | `plan-reviewer` | 구현 전 개발 계획 리뷰 - 리스크 평가, 갭 분석 |
| 9 | `planner` | `dev/active/`에 구조화된 개발 계획(plan/context/tasks) 생성 |
| 11 | `web-research-specialist` | GitHub Issues, Reddit, SO 등에서 기술 이슈 리서치 |

## 빠른 시작

### Backend

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .[dev]
./scripts/entrypoint.sh
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev  # http://localhost:3000
```
