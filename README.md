# Satie Cross-Modal AI Pipeline

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20085603.svg)](https://doi.org/10.5281/zenodo.20085603)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

에릭 사티(1866–1925)의 피아노 작품을 19세기 후반 파리 양식의 시각 예술로 번역합니다.

**기반 논문.** *Sonorous Brushstrokes: A Cross-Modal AI Framework for Translating Erik Satie's Fin-de-Siècle Parisian Solitude into Synaesthetic Visual Art* (`docs/Sonorous_Brushstrokes_v3_EN.docx`)

## 빠른 시작

```bash
# 1. 의존성 설치 (uv 권장)
uv sync
# 또는: pip install -e .

# 2. 사티 mp3 4개를 data/audio/에 드롭
#    (파일명에 gymnop / gnoss / vex 키워드만 들어 있으면 자동 매칭)

# 3. (선택) 시대 그림 jpg를 data/refs/에
#    예: puvis_sacred_grove.jpg, redon_closed_eyes.jpg, whistler_nocturne.jpg

# 4. 실행
uv run python -m src.generate
```

결과는 `data/outputs/`에 PNG로 저장됩니다 (곡당 약 60–90초, T4 GPU 기준).

## 옵션

```bash
# 한 곡만
uv run python -m src.generate --piece gymnopedie_1

# 시대 스타일 더 강하게 (참조 이미지 가중치 0.55 → 0.8)
uv run python -m src.generate --ip-adapter-scale 0.8

# 고해상도 (T4에서는 1024×1024가 한계)
uv run python -m src.generate --width 1024 --height 1024 --steps 40

# 참조 이미지 무시 (텍스트 프롬프트만으로 생성)
uv run python -m src.generate --no-ip-adapter
```

## 시스템 요구사항

- Python 3.10+
- CUDA-가능 GPU 12GB+ (16GB+ 권장 — T4, RTX 3060 12GB, RTX 4070+, A10/L4 등)
- 디스크 공간 ~10GB (모델 가중치)
- 첫 실행 시 모델 다운로드 ~7GB

CPU에서도 동작하지만 곡당 30분 이상 걸립니다 — 권장하지 않음.

## 해석 권한 — 어떻게 결과를 바꿀 수 있나

이 시스템의 해석적 선택은 두 파일에 명시적으로 박혀 있습니다:

- `src/bridge.py` — 음향 → 시각 어휘 매핑 규칙 (팔레트·구성·표면·분위기 4축)
- `src/prompts.py` — 곡별 주제 어구(`SUBJECT_PHRASES`) + 전기적 앵커(`BIOGRAPHICAL_ANCHORS`)

이 두 파일을 수정하는 것이 결과의 성격을 바꾸는 주된 방법입니다. 학습 가중치를 건드리지 않아도 됩니다.

## 디렉토리

```
src/             핵심 코드
docs/            논문 (.docx) + 자료 PDF
data/audio/      사티 mp3 (gitignore)
data/refs/       시대 그림 jpg (gitignore)
data/outputs/    생성 결과 PNG (gitignore)
```

## 참고 자료

- 논문 영문판: `docs/Sonorous_Brushstrokes_v3_EN.docx`
- 논문 한국어판: `docs/Sonorous_Brushstrokes_v3_KO.docx`
- 사티–발라동 1893 일대기 PDF: `docs/Bonjour_Biqui.pdf`

## 인용

```bibtex
@software{park_satie_cross_modal_2026,
  author       = {Park, Eun Ji},
  title        = {{satie-cross-modal: Cross-Modal AI Pipeline
                   Translating Erik Satie's Piano Works into
                   Fin-de-Si\`ecle Parisian Visual Art}},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.0.1},
  doi          = {10.5281/zenodo.20085603},
  url          = {https://doi.org/10.5281/zenodo.20085603}
}
```

GitHub의 "Cite this repository" 버튼으로도 BibTeX/APA 인용 메타데이터를 받을 수 있습니다 (`CITATION.cff` 기반).

## 라이선스

코드는 [MIT 라이선스](LICENSE) 하에 배포됩니다.
