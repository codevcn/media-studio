# Ghi chú về spotDL cho tính năng Spotify Downloader

Tài liệu này ghi lại lý do Media Studio dùng `spotDL` cho platform `spotify`, cách cài đặt `spotDL` trong project này, lỗi dependency đã gặp, và những thay đổi đã được thực hiện trong source code.

## 1. spotDL là gì?

`spotDL` là một công cụ dòng lệnh mã nguồn mở để tải nhạc từ link Spotify. Theo tài liệu chính thức, spotDL nhận link Spotify như track, album, playlist hoặc artist, sau đó tìm bản nhạc tương ứng từ nguồn audio khác như YouTube/YouTube Music, tải file audio về và gắn metadata như tên bài, nghệ sĩ, album art, lyrics.

Điểm quan trọng: spotDL không tải trực tiếp audio gốc từ Spotify. Nó dùng Spotify như nguồn metadata và dùng YouTube/YouTube Music làm nguồn audio khớp tương ứng.

Nguồn tham khảo:

- Trang chủ spotDL: https://spotdl.readthedocs.io/en/latest/
- Hướng dẫn cài đặt spotDL: https://spotdl.readthedocs.io/en/dev/installation/

## 2. Vì sao project cần spotDL cho Spotify?

Downloader hiện tại của Media Studio dùng `yt-dlp` cho đa số platform:

- YouTube / YouTube Music
- Facebook
- Instagram
- TikTok
- Douyin
- Bilibili
- SoundCloud

Khi thêm `spotify`, cách map thẳng sang `yt-dlp` không phù hợp vì Spotify không phải extractor chính thức ổn định trong pipeline hiện tại. Vì vậy phần Spotify được tách riêng:

- `soundcloud` vẫn dùng `yt-dlp + aria2c`.
- `spotify` dùng `spotdl download`.
- Spotify chỉ hỗ trợ luồng `audio`, không hỗ trợ `sub` hoặc video.

Lệnh Media Studio mong muốn:

```bash
mda dld spotify "https://open.spotify.com/playlist/..." audio --folder "D:\Music" --format mp3
```

## 3. Cách tích hợp trong source code

Các thay đổi chính đã thực hiện:

- `src/main.py`
  - Thêm action `spotify`.
  - Thêm action `soundcloud`.
  - Đưa hai action này vào danh sách platform hợp lệ của type `dld`.

- `src/features/downloader/run_downloader.py`
  - Import thêm `SoundCloudDownloader` và `SpotifyDownloader`.
  - Map `"soundcloud"` sang `SoundCloudDownloader`.
  - Map `"spotify"` sang `SpotifyDownloader`.

- `src/features/downloader/platform_downloaders.py`
  - Thêm `SoundCloudDownloader`, kế thừa `BaseDownloader`.
  - Thêm `SpotifyDownloader`, dùng `subprocess.run(["spotdl", "download", ...])`.
  - Với Spotify:
    - `--format` được truyền sang `spotdl --format`.
    - `--threads` được truyền sang `spotdl --threads`.
    - `--folder` và `--filename` được ghép thành `spotdl --output`.
    - `--cookies` được truyền sang `spotdl --cookie-file`.
    - `--cookies-from-browser` được truyền qua `spotdl --yt-dlp-args`.
    - Nếu thiếu `spotdl`, chương trình in hướng dẫn cài bằng `pipx`.

- `src/features/useful/print_feature_description.py`
  - Thêm `spotify` và `soundcloud` vào alias để `mda dld spotify --des` vẫn in đúng mô tả.

- `src/contents/help.txt`
  - Cập nhật danh sách platform downloader.
  - Thêm ví dụ SoundCloud và Spotify.

- `src/contents/app_features.yml`
  - Cập nhật mô tả chi tiết cho downloader.
  - Ghi rõ Spotify yêu cầu `spotdl` trong PATH và nên cài qua `pipx`.

- `README.md`
  - Cập nhật platform downloader.
  - Ghi `spotDL` là dependency tùy chọn cho Spotify.
  - Ghi cách cài `spotDL` bằng `pipx`.

## 4. Lỗi dependency đã gặp

Ban đầu `spotdl` được thêm vào `requirements.txt`. Sau đó chạy:

```bash
python -m pip install -r requirements.txt
```

Kết quả trong `log.log` cho thấy `pip` cài được `spotdl`, nhưng kéo theo dependency `fastapi 0.103.2`, dependency này yêu cầu `anyio<4.0.0,>=3.7.1`. Môi trường Python chính lúc đó lại đang có `google-genai 1.73.1`, yêu cầu `anyio>=4.8.0,<5.0.0`.

Xung đột chính:

```text
google-genai 1.73.1 requires anyio<5.0.0,>=4.8.0,
but you have anyio 3.7.1 which is incompatible.
```

Vì vậy quyết định cuối cùng là không để `spotdl` trong `requirements.txt` của project. `spotDL` là CLI app độc lập, nên nên cài bằng `pipx` để dependency của nó nằm trong virtual environment riêng.

## 5. Cách đã khôi phục môi trường Python chính

Sau khi thấy conflict, các bước khôi phục đã được thực hiện:

```bash
python -m pip uninstall -y spotdl fastapi
python -m pip install "anyio>=4.8,<5"
```

Sau đó kiểm tra:

```bash
python -m pip check
```

Conflict `google-genai` với `anyio` đã hết. Môi trường còn báo một conflict khác giữa `selenium` và `typing-extensions`, nhưng conflict đó không liên quan đến `spotDL`.

## 6. Cách cài spotDL đúng cho project này

Không dùng:

```bash
python -m pip install spotdl
```

Không thêm `spotdl` vào:

```text
requirements.txt
```

Cách khuyến nghị:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
python -m pipx install spotdl
```

Sau `ensurepath`, cần mở terminal mới để PATH nhận thêm thư mục chứa executable.

Theo log mới nhất, các lệnh này đã chạy thành công:

```text
Successfully installed argcomplete-3.6.3 pipx-1.11.1 userpath-1.9.2
Success! Added C:\Users\dell\AppData\Roaming\Python\Python312\Scripts to the PATH environment variable.
installed package spotdl 4.4.4, installed using Python 3.12.0
These apps are now available
  - spotdl.exe
done!
```

## 7. Vì sao pipx phù hợp hơn pip install trực tiếp?

`pipx` được thiết kế để cài các Python CLI app vào virtual environment riêng, rồi expose executable ra PATH. Điều này giúp app vẫn chạy được như lệnh toàn cục, nhưng dependency của app không làm bẩn hoặc phá môi trường Python chính.

Trong case này:

- Media Studio cần `google-genai` hoặc package khác trong Python chính giữ dependency riêng.
- `spotDL` cần dependency riêng của nó.
- `pipx install spotdl` giúp `spotdl.exe` chạy được toàn cục mà không downgrade `anyio` trong môi trường chính.

Nguồn tham khảo:

- Tài liệu pipx: https://pipx.pypa.io/latest/docs/
- Cách pipx hoạt động: https://pipx.pypa.io/stable/explanation/how-pipx-works/

## 8. Cách kiểm tra sau khi cài

Mở terminal mới rồi chạy:

```bash
where spotdl
spotdl --version
```

Sau đó thử qua Media Studio:

```bash
mda dld spotify "https://open.spotify.com/track/..." audio --format mp3
```

Nếu Media Studio báo không tìm thấy `spotdl`, thường là PATH chưa nhận thay đổi. Hãy mở terminal mới hoặc kiểm tra `python -m pipx ensurepath`.

## 9. Ghi chú về chất lượng và giới hạn

- Spotify trong Media Studio là audio-only.
- Kết quả phụ thuộc khả năng `spotDL` tìm đúng bản audio tương ứng từ YouTube/YouTube Music.
- `spotDL` có thể cần FFmpeg. Tài liệu chính thức ghi FFmpeg là yêu cầu cho spotDL.
- Người dùng chịu trách nhiệm về việc tải nội dung và tuân thủ bản quyền/nền tảng.

## 10. Checklist bảo trì sau này

Khi cần kiểm tra hoặc nâng cấp:

```bash
python -m pipx list
python -m pipx upgrade spotdl
```

Khi muốn gỡ:

```bash
python -m pipx uninstall spotdl
```

Khi sửa code Spotify downloader, nên kiểm tra lại:

```bash
python -m compileall -q src
python src\features\downloader\run_downloader.py spotify "https://open.spotify.com/track/test" audio
```

Lệnh test thứ hai không dùng link thật, nhưng đủ để kiểm tra nhánh lỗi khi thiếu `spotdl` hoặc kiểm tra chương trình có gọi được executable hay không.
