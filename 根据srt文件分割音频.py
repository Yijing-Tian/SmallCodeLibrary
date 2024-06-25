import re
import datetime
from pydub import AudioSegment

def parse_srt(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    subtitles = []
    pattern = re.compile(r'(\d+)\n(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\n(.+?)\n\n', re.DOTALL)
    matches = pattern.findall(srt_content)

    for match in matches:
        subtitle_id = int(match[0])
        start_time = datetime.timedelta(hours=int(match[1]), minutes=int(match[2]), seconds=int(match[3]), milliseconds=int(match[4]))
        end_time = datetime.timedelta(hours=int(match[5]), minutes=int(match[6]), seconds=int(match[7]), milliseconds=int(match[8]))
        content = match[9].strip()

        subtitles.append({
            'id': subtitle_id,
            'start_time': start_time,
            'end_time': end_time,
            'content': content
        })

    return subtitles

def split_audio_by_subtitles(audio_file, subtitles, output_dir):
    audio = AudioSegment.from_file(audio_file)

    for subtitle in subtitles:
        start_time = subtitle['start_time'].total_seconds() * 1000  # 转换为毫秒
        end_time = subtitle['end_time'].total_seconds() * 1000  # 转换为毫秒

        # 根据字幕信息分割音频
        segment = audio[start_time:end_time]

        # 将分割后的音频保存为文件
        output_file = f"{output_dir}/segment_{subtitle['id']}.wav"
        segment.export(output_file, format="wav")

        print(f"Segment {subtitle['id']} saved as {output_file}")


if __name__ == "__main__":
    audio_file = 'input.wav'
    subtitles_file = 'input.srt'
    output_dir = 'output'
    subtitles = parse_srt(subtitles_file)
    split_audio_by_subtitles(audio_file, subtitles, output_dir)