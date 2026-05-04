# Satie Cross-Modal AI Pipeline

## 프로젝트 개요

에릭 사티(Erik Satie, 1866–1925)의 피아노 작품을 19세기 후반 파리적 양식의 시각 예술로 번역하는 교차 모달(cross-modal) AI 파이프라인.

**핵심 아이디어.** 일반적인 "music-to-image" 시스템이 아니라:
1. **음향 특징 추출** (CLAP 의미 임베딩 + librosa 저수준 기술자)
2. **Lexical bridge** (음향 → 시각 어휘 핸드크래프트 규칙)
3. **전기적 앵커** (Biographical anchor — 곡이 발화한 사티 생애의 순간)
4. **시대 조건화 SDXL + IP-Adapter** (Symbolist / Nabis / 카바레 그래픽 참조)

자세한 프레임워크 정의는 `docs/Sonorous_Brushstrokes_v3_EN.docx`를 보세요.

## 대상 작품 (3곡)

| 곡 | 작곡 | 전기적 순간 |
|---|---|---|
| Gymnopédie No. 1 | 1888 | 발라동 연애 5년 전, Auberge du Clou 시기 |
| Gnossienne No. 1 | 1890 | 발라동 3년 전, 강화된 고독 |
| Vexations | 1893 후반 | 발라동 떠남 직후 (1893.6.20), 비탄의 강박 반복 |

## 디렉토리 구조

```
satie-cross-modal/
├── CLAUDE.md           # 이 파일 (Claude Code 컨텍스트)
├── README.md           # 사람용 빠른 시작
├── pyproject.toml      # Python 의존성 (uv)
├── src/
│   ├── audio.py        # 오디오 로딩 + 특징 추출
│   ├── bridge.py       # Lexical bridge (음향 → 시각 어휘)
│   ├── prompts.py      # PROMPTS, NEGATIVE, SUBJECT_PHRASES, BIOGRAPHICAL_ANCHORS
│   ├── pipeline.py     # SDXL + IP-Adapter 로딩
│   └── generate.py     # 메인 진입점 (CLI)
├── data/
│   ├── audio/          # 사티 mp3 4곡 (사용자 입력)
│   ├── refs/           # 시대 그림 jpg (사용자 입력, 선택사항)
│   └── outputs/        # 생성 이미지 (자동 생성)
└── docs/
    ├── Sonorous_Brushstrokes_v3_EN.docx   # 영문 논문
    ├── Sonorous_Brushstrokes_v3_KO.docx   # 한국어 논문
    └── Bonjour_Biqui.pdf                  # 사티–발라동 1893 일대기
```

## 주요 명령

```bash
# 환경 설정 (uv 사용)
uv sync

# 또는 pip 사용 시
pip install -e .

# 4곡 모두 생성
uv run python src/generate.py

# 한 곡만 생성
uv run python src/generate.py --piece gymnopedie_1

# 스타일 강도 조정
uv run python src/generate.py --ip-adapter-scale 0.7 --steps 40
```

## 입력 데이터 준비

### 음원 (필수)

`data/audio/` 폴더에 사티 mp3 3개:
- `gymnopedie_1.mp3` (또는 파일명에 "gymnop" 포함)
- `gnossienne_1.mp3` (또는 "gnoss" 포함)
- `vexations.mp3` (또는 "vex" 포함)

권장 출처:
- [IMSLP](https://imslp.org/wiki/Category:Satie,_Erik) — CC 라이선스 연주
- [Musopen](https://musopen.org/music/composer/erik-satie/)
- [Piano Society](https://pianosociety.com/) — Chase Coleman 등 무료 기증 연주

### 참조 이미지 (선택)

`data/refs/` 폴더에 jpg/png. 비어 있으면 IP-Adapter 자동 비활성화.

권장 작품 (Wikimedia Commons에서 직접 다운로드):
- `puvis_sacred_grove.jpg` — Pierre Puvis de Chavannes, *Le Bois sacré*
- `redon_closed_eyes.jpg` — Odilon Redon, *Les Yeux clos*
- `moreau_galatea.jpg` — Gustave Moreau, *Galatée*
- `whistler_nocturne.jpg` — Whistler, *Nocturne in Blue and Silver*

## 알려진 함정

1. **numpy ABI 충돌**: librosa 0.10.x는 numpy<2를 요구하지만, 최신 diffusers/torch는 numpy 2.x용으로 컴파일됨. **해결:** `librosa>=0.11` 사용 (`pyproject.toml`에 명시됨).
2. **librosa.beat.tempo 제거**: librosa 0.11+에서 `librosa.feature.tempo`로 이동. `_tempo()` 헬퍼가 양쪽 호환.
3. **GPU VRAM**: SDXL + IP-Adapter는 12GB+ 필요. 8–12GB GPU에서는 `pipe.enable_sequential_cpu_offload()` 사용.
4. **Wikimedia 직접 다운로드**: 자동 스크립트 요청은 403 거부됨. 브라우저로 수동 다운로드 후 `data/refs/`에 배치.

## 아키텍처 결정

- **Lexical bridge는 학습 함수가 아니라 핸드크래프트 규칙.** 감사 가능성(auditability)과 해석 권한을 사람 손에 두기 위함. `src/bridge.py`에 모든 규칙이 명시되어 있음.
- **Biographical anchor는 하이퍼파라미터.** 곡별 어구는 `src/prompts.py`의 `BIOGRAPHICAL_ANCHORS`에 명시. 이는 음악학자와의 협업 결과이며, 다른 해석을 시도하려면 이 dict만 바꾸면 됨.
- **이미지 크기 768×768 기본.** T4 GPU에서 곡당 약 60초. 1024로 올리려면 `--width 1024 --height 1024`.

## 다음 작업 후보

- [ ] Vexations 시퀀스 모드 (12시간 렌더링 → 24 프레임)
- [ ] 라이브 피아니스트 입력 → 실시간 이미지 변조 (Streamlit)
- [ ] 추가 곡 — Pièces froides, Embryons desséchés
- [ ] 「Bonjour Biqui Bonjour」 30초 한계 사례 — 텍스트 스캐폴딩 강화

