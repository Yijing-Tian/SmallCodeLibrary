from datetime import datetime

def parse_srt(filename):
    subtitles = []
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 4):
            index = int(lines[i].strip())
            start_str, end_str = lines[i + 1].strip().split(' --> ')
            text = lines[i + 2].strip()
            start_time = datetime.strptime(start_str, '%H:%M:%S,%f')
            end_time = datetime.strptime(end_str, '%H:%M:%S,%f')
            subtitles.append((index, start_time, end_time, text))
    return subtitles

def merge_subtitles(subtitles, min_interval_ms=800, min_merge_count=2, max_merge_count=5):
    merged_subtitles = []
    current_subs = []
    for index, start, end, text in subtitles:
        if not current_subs:
            current_subs.append((start, end, text))
        else:
            interval = (start - current_subs[-1][1]).total_seconds() * 1000
            if interval <= min_interval_ms and len(current_subs) < max_merge_count:
                current_subs.append((start, end, text))
            else:
                if len(current_subs) >= min_merge_count:
                    merged_subtitles.append(merge(current_subs))
                current_subs = [(start, end, text)]
    if len(current_subs) >= min_merge_count:
        merged_subtitles.append(merge(current_subs))
    return merged_subtitles

def merge(subs):
    start = subs[0][0]
    end = subs[-1][1]
    text = ','.join(sub[2] for sub in subs)
    return start, end, text

def save_srt(filename, subtitles):
    with open(filename, 'w', encoding='utf-8') as file:
        for i, (start, end, text) in enumerate(subtitles, 1):
            file.write(str(i) + '\n')
            file.write(start.strftime('%H:%M:%S,%f')[:-3] + ' --> ' + end.strftime('%H:%M:%S,%f')[:-3] + '\n')
            file.write(text + '\n\n')

# def parse_srt_text(filename, output_filename): # 给gptsovits或bertvits用
#     text = ""
#     index = 0
#     with open(filename, 'r', encoding='utf-8') as file:
#         lines = file.readlines()
#         for i in range(2, len(lines), 4):  # start from index 2 and skip every 4 lines
#             text += f"./raw/zenglao/zenglao_{index}.wav|zenglao|ZH|{lines[i].strip()}\n"
#             index += 1
#     with open(output_filename, 'w', encoding='utf-8') as file:
#         file.write(text)

if __name__ == "__main__":
    input_filename = "input.srt"
    output_filename = "output.srt"
    subtitles = parse_srt(input_filename)
    merged_subtitles = merge_subtitles(subtitles)
    save_srt(output_filename, merged_subtitles)
    # parse_srt_text(output_filename, "result.txt")