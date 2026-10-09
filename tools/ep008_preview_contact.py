"""Build EP008 visual review sheets from full-resolution preview renders."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
PREVIEWS = ROOT / '02_EPISODES/EP008_Research_Then_Now/previews'
FRAMES = [25, 85, 193, 217, 337, 433, 481, 505, 529, 565, 571, 576]
BEATS = ['Book opening', 'Notes', 'Success beat', 'Hard cut', 'Frantic typing',
         'Rabbit hole', 'Nested sources', 'Freeze', 'Source question',
         'Overload', 'Desk impact', 'Final hold']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    available = [(frame, beat, PREVIEWS / f'EP008_Review_{frame:04d}.png')
                 for frame, beat in zip(FRAMES, BEATS)]
    missing = [str(path) for _, _, path in available if not path.exists()]
    if missing and not args.allow_partial:
        raise FileNotFoundError('Missing preview frames: ' + ', '.join(missing))
    available = [item for item in available if item[2].exists()]
    if not available:
        raise FileNotFoundError('No EP008 preview frames are available yet')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    width, height, label_height = 270, 480, 46
    columns = 4
    rows = (len(available) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * width, rows * (height + label_height)), '#171b24')
    draw = ImageDraw.Draw(sheet)
    for index, (frame, beat, path) in enumerate(available):
        column, row = index % columns, index // columns
        x, y = column * width, row * (height + label_height)
        with Image.open(path) as image:
            if image.size != (1080, 1920):
                raise ValueError(f'Unexpected review dimensions: {path}: {image.size}')
            sheet.paste(image.convert('RGB').resize((width, height), Image.Resampling.LANCZOS),
                        (x, y + label_height))
        draw.text((x + 8, y + 4), f'{(frame - 1) / 24:.3f}s / frame {frame}',
                  fill='#ffffff', font=font)
        draw.text((x + 8, y + 25), beat, fill='#b4c4dd', font=small)
    target = PREVIEWS / 'EP008_Review_Contact_Sheet.png'
    sheet.save(target)
    print(str(target), flush=True)

    # Important source-note/desk-impact frames at phone-readable review scale.
    final = [item for item in available if item[0] in (529, 565, 571, 576)]
    if final:
        detail = Image.new('RGB', (540 * len(final), 1006), '#171b24')
        dd = ImageDraw.Draw(detail)
        for index, (frame, beat, path) in enumerate(final):
            with Image.open(path) as image:
                detail.paste(image.convert('RGB').resize((540, 960), Image.Resampling.LANCZOS),
                             (index * 540, label_height))
            dd.text((index * 540 + 8, 4), f'{(frame - 1) / 24:.3f}s / frame {frame}',
                    fill='#ffffff', font=font)
            dd.text((index * 540 + 8, 25), beat, fill='#b4c4dd', font=small)
        target = PREVIEWS / 'EP008_Final_Beats_Contact_Sheet.png'
        detail.save(target)
        print(str(target), flush=True)


if __name__ == '__main__':
    main()
