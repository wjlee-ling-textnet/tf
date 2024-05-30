# Chunky

## How to

### 1. Parse and extract elements

`python -m parsers.pdf [pdf_path] -fn=parse_pdf_fitz -save_dir=[저장 경로] -tc={'output_format':'csv'}`

#### arguments

- `-fn:` function (parser) to use

  - `parse_pdf_fitz` only for now

- `-save_dir`: save path
- `-page`
  - `all`
  - page number: e.g. `3`
  - range: e.g.`1-5`
- `-ic` (`--image_config`)
  - `output_dir` : `-save_dir` 내 추출된 이미지 폴더 (default: `images/`)
- `-tc` (`--table_config`)
  - `output_dir` : `-save_dir` 내 파싱된 csv 파일 저장 폴더 (default: `tables/`)
  - `strategy` : fitz 용 테이블 인식 전략
    - `lines` (default)
    - `text`
    - `strict_lines`
  - `horizontal_strategy`
  - `vertical_strategy`
  - `output_format`
    - `csv` : `output_dir`에 저장
    - `dataframe`
    - `markdown`

#### results

![extract_parsed](https://github.com/wjlee-ling/Talk2Me/assets/61496071/ea9e838c-e419-4801-9da4-d628d6ac3aa1)

### 2. Augment manually

작업자가 추출된 요소들 검수 및 수정 후 덮어쓰기

### 3. Post-process

`python -m parsers.postprocessors [path]`

- 테이블 하이퍼링크를 그 내용으로 대체
- TODO: 들여쓰기 기준 텍스트 재구조화

#### arguments

- `path`
- `--output_dir` : 수정된 텍스트 파일 결과물 (default `output/`)
- `--output_format` :
  - `markdown` (default)

#### results

![postprocess](https://github.com/wjlee-ling/Talk2Me/assets/61496071/05b14779-adfb-4579-9658-c425f8da9737)
