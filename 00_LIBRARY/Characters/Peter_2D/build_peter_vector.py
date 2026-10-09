"""Rebuild Peter's curated editable vector portrait and Grease Pencil contours.

Pure Python source, no image embedding or runtime path assumptions. The SVG has
semantic groups; sampled contours retain the exact same painter's order.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
INK = "#191A21"
SKIN = "#EFAE7D"
SHADOW = "#BD7D58"
HAIR = "#3C2B24"
HAIR_LIGHT = "#634332"
HOODIE = "#28314B"
PATHS = []
EXPRESSIONS = {"mouth": {}, "eyes": {}}


def path(group, ident, d, fill, stroke=None, width=0):
    record = {"group": group, "id": ident, "d": d, "fill": fill,
              "stroke": stroke, "stroke_width": width}
    PATHS.append(record)
    return record


def expression(category, label, records):
    EXPRESSIONS[category][label] = [dict(record) for record in records]


def p(ident, d, fill, stroke=INK, width=5):
    return {"group": "mouth", "id": ident, "d": d, "fill": fill,
            "stroke": stroke, "stroke_width": width}


# Hoodie and undershirt; intentionally separate from the reusable head.
path("hoodie", "hoodie_silhouette", "M0 1254 L29 1135 L169 1058 L172 1027 L249 921 L325 899 L382 842 L470 805 L811 778 Q903 779 954 807 L1007 884 L1062 891 L1101 941 L1165 985 L1172 1023 L1254 1068 L1254 1254 Z", HOODIE, INK, 9)
path("hoodie", "hoodie_left_shadow", "M173 1055 L250 940 L317 925 L352 1066 L369 1099 L295 1004 L258 944 L205 1028 Z", "#20263C")
path("hoodie", "hoodie_left_lapel", "M473 810 L409 858 L436 964 L540 1246 L411 1195 L415 1163 L293 1117 L218 1078 L292 930 L405 827 Z", "#303A58", "#22263A", 6)
path("hoodie", "hoodie_right_lapel", "M812 781 Q871 792 909 830 L878 916 L819 1029 L765 1112 L851 1068 L1009 910 L954 808 Q905 781 812 781 Z", "#22283E", INK, 5)
path("hoodie", "hoodie_right_outer_lapel", "M1007 886 L1035 916 L1003 972 L929 1060 L886 1081 L1171 1025 L1165 985 L1100 943 L1066 891 Z", "#303953", "#22263A", 5)
path("hoodie", "shirt", "M472 1043 Q638 1093 794 1027 L672 1254 L544 1254 Z", "#D9CEC7", INK, 6)
path("hoodie", "shirt_fold", "M502 1098 Q624 1127 765 1084", None, "#A89C97", 6)
path("hoodie", "left_cuff_fold", "M105 1180 L110 1254 L133 1254 Z", "#1D253D")
path("hoodie", "right_hood_fold", "M867 1144 L831 1254 L811 1254 L835 1154 Z", "#1D253D")
path("hoodie", "right_outer_fold", "M1193 1113 L1209 1125 L1189 1254 L1167 1254 Z", "#22283E")

# Neck, ears and the distinctive off-centre face silhouette.
path("neck", "neck", "M459 700 L812 683 L833 886 L875 902 L792 1033 Q646 1097 478 1047 L459 1008 L494 916 L477 838 Z", SKIN, INK, 6)
path("neck", "neck_shadow", "M485 723 L570 770 L669 798 L784 762 L770 800 L720 833 Q675 852 635 856 L563 791 Z", SHADOW)
path("neck", "neck_left_shadow", "M549 913 L583 1023 L607 1039 L581 979 Z", "#C5875D")
path("neck", "neck_line_left", "M476 837 L499 941 L495 876", "#22242F")
path("neck", "neck_line_right", "M813 781 L836 904 L827 886", "#22242F")
path("ears", "ear_left", "M349 492 Q313 494 301 542 L321 595 Q340 628 389 646 L441 644 L436 520 Z", SKIN, INK, 7)
path("ears", "ear_left_shadow", "M343 520 Q328 522 326 544 L335 577 L344 553 L369 558 Q354 577 368 594 L384 610 L409 610 L408 597 L391 580 L393 553 Z", "#BA7854")
path("ears", "ear_left_inner", "M344 524 Q332 526 330 546 L341 534 L371 551 L387 554 L383 578 L400 596", None, "#9D6549", 5)
path("ears", "ear_right", "M838 437 Q873 422 888 444 Q902 466 901 506 L889 554 Q875 583 839 586 L822 534 Z", SKIN, INK, 7)
path("ears", "ear_right_shadow", "M861 447 Q883 445 884 468 L885 496 L875 477 L859 486 Q869 500 869 515 Q869 535 849 547 L841 531 L849 492 Z", "#BD7D58")
path("ears", "ear_right_inner", "M863 448 L882 468 L883 488 L867 473 L848 487 L860 503 Q875 527 847 544", None, "#A56B4D", 4)
path("hair", "back_hair_left", "M433 628 L443 655 L471 737 L453 731 L438 715 L435 726 L421 706 L407 700 L391 700 L405 684 L414 655 Z", HAIR, INK, 6)
path("hair", "back_hair_shade", "M417 645 L439 695 L454 711 L446 726 L432 707 L425 716 L416 694 L405 696 L413 679 Z", "#211E1F")
path("face", "face_silhouette", "M438 280 Q536 210 700 210 L769 233 L795 261 Q832 305 837 382 L845 490 L840 580 L837 641 Q832 675 812 706 L744 779 Q710 791 653 795 Q601 792 554 761 L479 712 L438 651 L417 595 L409 500 L409 410 L435 384 L433 317 Z", SKIN, INK, 6)
path("face", "face_left_tone", "M432 320 L472 283 L478 308 L448 352 L434 384 L425 433 L417 496 L410 502 L410 411 L435 385 Z", "#E4A173")
path("face", "jaw_right_tone", "M832 570 L837 622 Q837 660 815 697 L746 776 L695 785 L745 765 L803 694 Q826 655 828 606 Z", "#E6A371")
path("face_detail", "forehead_line_1", "M585 318 Q644 317 681 303 Q708 293 731 293", None, "#C98B64", 4)
path("face_detail", "forehead_line_2", "M552 350 Q583 339 614 343 Q646 346 668 336 L707 323", None, "#D39368", 4)
path("face_detail", "temple_shadow_left", "M526 423 L587 417 L608 427 L624 443 L603 454 L579 437 Z", "#C88B64")
path("face_detail", "temple_shadow_right", "M694 398 Q719 389 745 398 L777 400 Q740 403 707 414 L678 443 L680 418 Z", "#C88B64")

# Brows: individual filled tapered shapes maintain the reference expression.
path("brows", "brow_left", "M455 444 L479 414 L500 401 L586 385 L602 400 L570 407 L505 415 L478 427 Z", "#392B26")
path("brows", "brow_left_highlight", "M486 412 L528 399 L566 397 L529 406 L502 409 Z", "#71503B")
path("brows", "brow_right", "M692 382 L699 363 L772 345 L793 355 L814 375 L775 360 L740 367 Z", "#352821")
path("brows", "brow_right_highlight", "M708 362 L769 350 L787 357 L753 358 L719 367 Z", "#71503B")

# Eye groups remain separate so blink drawings replace only these paths.
path("eyes", "eye_left_white", "M489 489 Q496 463 529 451 Q560 439 582 456 Q598 471 595 494 Q577 514 545 516 Q511 517 492 502 Z", "#F0ECE8", INK, 5)
path("eyes", "eye_left_iris", "M573 452 Q595 457 593 480 Q592 502 576 503 Q556 501 554 481 Q552 460 573 452 Z", "#43302A", INK, 3)
path("eyes", "eye_left_pupil", "M576 464 Q587 464 587 479 Q586 491 576 491 Q566 490 566 477 Q566 466 576 464 Z", "#14151B")
path("eyes", "eye_right_white", "M703 462 Q709 427 747 417 Q781 412 793 434 Q801 452 791 469 Q775 484 746 484 Q715 483 702 472 Z", "#F3EFEB", INK, 5)
path("eyes", "eye_right_iris", "M776 424 Q794 429 793 450 Q791 474 776 474 Q756 472 756 448 Q756 427 776 424 Z", "#3D2B25", INK, 3)
path("eyes", "eye_right_pupil", "M777 436 Q786 436 786 449 Q785 462 776 461 Q768 458 768 448 Q768 438 777 436 Z", "#111319")
path("eyes", "left_lid_fold", "M485 472 Q503 437 549 433 Q575 430 590 448", None, "#282126", 3)
path("eyes", "right_lid_fold", "M689 425 Q710 398 744 401 Q779 400 794 420", None, "#282126", 3)
path("face_detail", "eye_left_under", "M534 534 Q563 532 590 507", None, "#C4835B", 4)
path("face_detail", "eye_right_under", "M714 491 Q746 507 776 499", None, "#C4835B", 4)

# Nose and a tiny cheek mole are identity details, not generic emoji features.
path("nose", "nose_shadow", "M627 565 L623 588 L638 596 L653 591 L675 598 L691 595 L714 578 L714 556 L701 570 L685 579 L664 572 L643 578 Z", "#BD7D55")
path("nose", "nose_bridge", "M684 414 L670 461 L693 530 L714 556 L714 577 L705 581", None, INK, 4)
path("nose", "nostril_left", "M626 566 L624 587 L634 590 L655 582 L668 586", None, INK, 4)
path("nose", "nostril_right", "M689 594 L699 578 L708 577", None, INK, 4)
path("face_detail", "cheek_mole", "M812 586 Q812 589 809 589 Q806 587 808 584 Q811 582 812 586 Z", "#BE7C57")
path("face_detail", "upper_lip_shadow", "M601 650 Q646 633 670 638 Q704 629 746 637 L716 647 L650 653 Z", "#CA8B65")
path("mouth", "mouth_smile", "M594 659 Q635 645 674 640 L746 637 Q721 655 694 661 Q650 671 621 664 Z", "#231E20", INK, 4)
path("mouth", "mouth_teeth", "M617 657 Q660 647 705 646 L715 645 Q699 657 675 659 Q642 663 617 657 Z", "#F0E7E0")
path("face_detail", "chin_shadow", "M653 689 L708 682 L697 696 L664 701 Z", "#BB7D58")

# Front hair is a deliberately curated layered vector silhouette, not a bitmap.
path("hair", "front_hair_silhouette", "M419 558 L391 531 L382 507 L358 517 L337 513 L305 518 L288 489 L288 460 L267 440 L268 393 L248 382 L271 326 L252 323 L250 264 L298 233 Q281 215 295 183 Q298 204 310 212 L326 153 L362 123 L399 116 L425 79 L500 48 L547 48 L571 40 L612 42 L649 29 L670 62 L719 68 L736 88 Q766 77 794 81 L827 134 L817 143 Q853 143 875 166 L884 204 L894 229 L890 261 L912 283 L898 298 L883 300 L893 325 L918 320 L905 346 L885 358 L890 376 L879 396 L887 409 L873 425 L863 423 L849 449 L839 478 L833 389 L821 322 L797 266 L759 227 L710 239 L735 215 L676 240 L696 215 L650 247 L632 257 L586 256 L509 267 Q506 307 532 332 Q500 329 484 307 Q479 293 479 279 L434 318 L434 385 L409 419 L409 510 Z", HAIR, INK, 7)
path("hair", "hair_top_light", "M325 152 L365 127 L401 125 L429 88 L501 61 L540 59 L507 82 L453 100 L417 153 L444 144 L477 103 L520 86 Q587 55 654 53 L666 66 Q727 76 749 108 L747 161 L720 211 L673 238 Q706 197 690 157 Q679 119 649 114 L598 110 L552 133 L582 121 L624 133 L646 171 L643 240 L631 248 L624 203 L589 171 L564 159 L535 187 L510 229 L503 269 L518 313 L499 300 Q486 267 493 229 L466 251 L438 291 L394 316 L380 318 L433 261 L460 241 L478 237 L490 205 L458 228 L438 246 L395 282 L349 291 L326 315 L280 364 L297 322 L300 286 L333 275 L395 218 L347 228 L313 250 L275 301 L277 268 L308 246 L323 218 L315 211 Z", HAIR_LIGHT)
path("hair", "hair_crown_highlight", "M430 85 L500 56 L537 56 L503 73 L462 81 L442 101 L416 133 Z", "#78513B")
path("hair", "hair_crown_ridge", "M542 70 Q582 49 621 57 L651 41 L665 62 L645 61 L625 68 Q582 64 542 70 Z", "#513B2D")
path("hair", "hair_crown_lower", "M501 80 Q570 63 642 73 L676 93 L648 111 L598 110 L552 133 L576 108 Q532 113 493 138 L442 184 L480 129 Z", "#704A35")
path("hair", "hair_left_center_lock", "M305 294 Q334 314 374 296 L397 289 L377 318 L341 347 L297 321 Z", "#352822")
path("hair", "hair_left_center_shine", "M316 273 L346 244 L394 218 L382 232 L400 232 L423 223 L412 245 L386 261 L377 279 L344 295 Z", "#493226")
path("hair", "hair_left_inner_lock", "M339 346 L369 348 L402 330 L388 354 L358 367 L313 369 L296 391 L275 419 L275 386 L309 365 Z", "#6A4532")
path("hair", "hair_left_mid_shadow", "M285 404 L344 389 L374 370 L403 359 L393 385 L344 412 L311 422 L298 437 L280 446 Z", "#352823")
path("hair", "hair_left_mid_glint", "M296 448 Q332 448 364 429 L381 414 L406 395 L396 419 L374 443 L341 465 L309 470 L289 460 Z", "#4C3428")
path("hair", "hair_left_low_lock", "M289 473 L322 488 L356 481 L377 465 L389 448 L386 483 L358 498 L319 500 L300 491 Z", "#65422F")
path("hair", "hair_left_low_shadow", "M302 503 L339 507 L361 496 L387 478 L380 506 L359 513 L338 510 L315 516 Z", "#241F1E")
path("hair", "hair_left_sideburn", "M380 491 L397 478 L403 509 L419 556 L397 534 L389 520 Z", "#28201E")
path("hair", "hair_fringe_shadow", "M552 209 L586 224 L614 243 L626 251 L586 245 L594 257 L551 252 L510 264 Q507 291 519 310 L531 329 L516 324 L498 306 L487 281 L491 246 L511 210 L542 161 L576 154 L592 156 L620 169 L631 211 L630 248 L615 213 L594 182 L581 184 L600 217 L609 237 Z", "#251F1E")
path("hair", "hair_fringe_glint", "M547 210 L576 235 L583 240 L559 238 L567 246 L514 258 L523 226 Z", "#4B3126")
path("hair", "hair_fringe_streak", "M477 279 L484 303 Q493 323 521 335 L507 333 Q479 325 475 303 Z", "#B7774E")
path("hair", "hair_right_top_lock", "M741 93 L776 89 L794 93 L821 133 L807 147 L790 143 L775 166 L764 192 L728 227 L710 239 L737 187 L750 137 L747 111 Z", "#634532")
path("hair", "hair_right_top_shadow", "M770 97 L784 134 L771 169 L759 199 L720 233 L741 190 L750 157 L750 111 Z", "#2B231F")
path("hair", "hair_right_top_shine", "M777 89 L793 86 L817 127 L810 130 L795 105 Z", "#73503C")
path("hair", "hair_right_sweep", "M795 155 L824 149 L850 154 L868 169 L880 207 L856 188 L840 174 L811 169 L786 177 L806 163 Z", "#593C2D")
path("hair", "hair_right_sweep_shadow", "M774 223 Q790 204 814 198 Q849 198 877 230 L879 248 L858 229 L836 215 L815 211 L792 214 Z", "#30241E")
path("hair", "hair_right_upper_glint", "M797 223 L821 216 L847 223 L868 243 L887 279 L905 286 L893 295 L870 287 L854 258 L833 239 Z", "#61402F")
path("hair", "hair_right_temples", "M780 247 L810 250 L832 276 L859 310 L876 319 L893 326 L911 325 L902 342 L888 351 L864 345 L842 327 L819 292 Z", "#55382B")
path("hair", "hair_right_temples_shadow", "M818 295 L843 317 L859 340 L887 354 L895 366 L885 378 L863 368 L851 356 L834 330 Z", "#30251F")
path("hair", "hair_right_lower_lock", "M844 351 L862 374 L875 382 L887 394 L879 403 L865 408 L854 395 L849 390 Z", "#61412F")
path("hair", "hair_right_sideburn", "M850 399 L866 416 L858 435 L846 458 L839 476 L836 431 Z", "#27201E")

# Mouth drawings are designed around one shared pivot (670,651).
expression("mouth", "rest", [p("mouth_rest", "M601 659 Q671 644 740 638", None, INK, 5)])
expression("mouth", "MBP", [p("mouth_mbp", "M604 653 Q646 659 681 651 Q711 644 739 641", None, INK, 6)])
expression("mouth", "AA", [p("mouth_aa", "M611 644 Q663 626 727 638 Q724 681 686 691 Q640 695 611 644 Z", "#422326"), p("mouth_aa_teeth", "M619 643 Q669 633 720 641 L713 653 Q660 650 624 654 Z", "#F5EAE2", None, 0), p("mouth_aa_tongue", "M649 681 Q676 664 700 679 Q679 695 649 681 Z", "#C66D75", None, 0)])
expression("mouth", "EE", [p("mouth_ee", "M595 651 Q663 627 745 638 Q735 670 675 675 Q625 673 595 651 Z", "#432528"), p("mouth_ee_teeth", "M606 648 Q669 634 738 641 L728 654 Q669 660 616 657 Z", "#F6EAE2", None, 0)])
expression("mouth", "OH", [p("mouth_oh", "M655 626 Q685 620 697 646 Q709 679 684 692 Q655 701 644 674 Q633 643 655 626 Z", "#422326"), p("mouth_oh_tongue", "M656 680 Q673 670 690 682 Q674 695 656 680 Z", "#C66D75", None, 0)])
expression("mouth", "FV", [p("mouth_fv", "M603 652 Q661 637 740 640 Q714 662 675 665 Q634 666 603 652 Z", "#422326"), p("mouth_fv_teeth", "M618 648 Q672 638 731 644 L711 654 Q662 658 627 655 Z", "#F6EAE2", None, 0)])
expression("mouth", "smile", [record for record in PATHS if record["group"] == "mouth"])
expression("eyes", "blink", [{"group": "eyes", "id": "eye_left_closed", "d": "M490 485 Q535 506 593 479", "fill": None, "stroke": INK, "stroke_width": 6}, {"group": "eyes", "id": "eye_right_closed", "d": "M702 456 Q747 476 793 449", "fill": None, "stroke": INK, "stroke_width": 6}])


def sample_path(d):
    tokens = re.findall(r"[MLCQZmlcqz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d)
    output, i, point, start, closed = [], 0, (0., 0.), None, False
    command = None
    while i < len(tokens):
        if tokens[i].isalpha():
            command = tokens[i]
            i += 1
        if command == "Z":
            closed = True
            break
        count = {"M": 2, "L": 2, "Q": 4, "C": 6}[command]
        values = [float(v) for v in tokens[i:i + count]]
        i += count
        if command in {"M", "L"}:
            point = tuple(values)
            output.append(point)
            if command == "M":
                start, command = point, "L"
        else:
            controls = [point] + [tuple(values[k:k + 2]) for k in range(0, len(values), 2)]
            length = sum(math.dist(a, b) for a, b in zip(controls, controls[1:]))
            segments = max(4, min(50, math.ceil(length / 10)))
            for n in range(1, segments + 1):
                t = n / segments
                if command == "Q":
                    xy = tuple((1-t)**2*controls[0][a] + 2*(1-t)*t*controls[1][a] + t*t*controls[2][a] for a in range(2))
                else:
                    xy = tuple((1-t)**3*controls[0][a] + 3*(1-t)**2*t*controls[1][a] + 3*(1-t)*t*t*controls[2][a] + t**3*controls[3][a] for a in range(2))
                output.append(xy)
            point = controls[-1]
    return [[round(x, 3), round(y, 3)] for x, y in output], closed


def contour(record):
    points, closed = sample_path(record["d"])
    value = {key: value for key, value in record.items() if key != "d"}
    # SVG fills implicitly close subpaths even when the source omits a Z.
    value.update(points=points, closed=closed or record["fill"] is not None)
    value["fill_rgba"] = rgba(record["fill"])
    value["stroke_rgba"] = rgba(record["stroke"])
    return value


def rgba(hex_color):
    if hex_color is None:
        return None
    return [round(int(hex_color[a:a + 2], 16) / 255, 6) for a in (1, 3, 5)] + [1.0]


def svg_path(record):
    return '<path id="{id}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>'.format(**{**record, "fill": record["fill"] or "none", "stroke": record["stroke"] or "none"})


def make_svg(records, *, background=False):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1254 1254" width="1254" height="1254" role="img" aria-labelledby="title description">', '<title id="title">Peter — editable vector character</title>', '<desc id="description">Curated layered vector interpretation of the user-supplied portrait. Brown tousled hair, warm skin, navy hoodie; semantic groups for animation. No embedded raster image.</desc>']
    if background:
        lines.append('<rect width="1254" height="1254" fill="#CE7045"/>')
    group = None
    group_counts = {}
    for record in records:
        if group != record["group"]:
            if group is not None:
                lines.append('</g>')
            group = record["group"]
            group_counts[group] = group_counts.get(group, 0) + 1
            suffix = "" if group_counts[group] == 1 else "_" + str(group_counts[group])
            lines.append('<g id="feature_{}" data-feature="{}">'.format(escape(group + suffix), escape(group)))
        lines.append(svg_path(record))
    if group is not None:
        lines.append('</g>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def write_assets():
    (HERE / "Peter_2D_v001.svg").write_text(make_svg(PATHS), encoding="utf-8")
    rest = [record for record in PATHS if record["group"] != "mouth"]
    # Rest is inserted before front hair; no visual overlap in that region.
    rest += EXPRESSIONS["mouth"]["rest"]
    (HERE / "Peter_2D_Rest_v001.svg").write_text(make_svg(rest), encoding="utf-8")
    manifest = {"schema_version": 1, "character": "Peter", "source": "User-supplied Stylized Tom Holland Cartoon Portrait.png", "view_box": [0, 0, 1254, 1254], "coordinates": "image-space; x right, y down; colors are sRGB; painter order matters", "head_pivot": [627, 495], "mouth_pivot": [670, 651], "face_bounds": [301, 25, 918, 798], "paths": [contour(record) for record in PATHS], "expressions": {category: {label: [contour(record) for record in records] for label, records in variants.items()} for category, variants in EXPRESSIONS.items()}}
    (HERE / "Peter_2D_Paths_v001.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(PATHS)} editable paths and {sum(len(v) for v in EXPRESSIONS.values())} expression variants.")


if __name__ == "__main__":
    write_assets()
