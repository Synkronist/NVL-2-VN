# =============================================
# Full-Screen 1080p Kinetic Novel Reader
# Features:
#  - Preload all pages at startup (exact page count)
#  - Adjustable font size (+ / -)
#  - Smooth fade ONLY when background changes
#  - Now Playing OST X (top center)
#  - Word count + total words + estimated time left (bottom left)
#  - Page X of Y (bottom center, exact)
#  - Left/Right skip 5 pages
#  - Track selector (press M)
#  - Loading screen with bg1.png
# =============================================

default page_history = []
default bookmark_page = None
default current_bg_index = 0
default reader_font_size = 20
default current_track = 0
default wpm = 250
default total_words = 0
default total_pages = 0
default all_pages = []

# ============================================================
# INIT PYTHON — TEXT HANDLING + LISTS
# ============================================================
init python:
    import math

    backgrounds = [f"images/bg{i}.png" for i in range(1, 32)]
    playlist = [f"audio/ost{i}.mp3" for i in range(1, 21)]

    def escape_for_renpy(text):
        return (
            text.replace("{", "{{")
                .replace("}", "}}")
                .replace("[", "[[")
                .replace("]", "]]")
        )

    def read_paragraph(file_handle):
        lines = []
        while True:
            line = file_handle.readline()
            if not line:
                break
            stripped = line.strip()
            if stripped == "":
                if lines:
                    break
                else:
                    continue
            lines.append(stripped)
        if not lines:
            return None
        return " ".join(lines)

    def estimate_lines(text, chars_per_line=95):
        return max(1, math.ceil(len(text) / chars_per_line))

    def paginate_file(path, max_lines=34):
        """Reads entire file and returns a list of pages."""
        fh = renpy.open_file(path, encoding="utf-8")
        pages = []
        buffer = []
        used_lines = 0

        while True:
            para = read_paragraph(fh)
            if para is None:
                if buffer:
                    pages.append("\n\n".join(buffer))
                break

            safe = escape_for_renpy(para)
            needed = estimate_lines(safe)

            if used_lines + needed > max_lines:
                pages.append("\n\n".join(buffer))
                buffer = [safe]
                used_lines = needed + 1
            else:
                buffer.append(safe)
                used_lines += needed + 1

        fh.close()
        return pages

    def count_words(s):
        return len(s.split()) if s else 0


# ============================================================
# TRANSITIONS / STYLES
# ============================================================
define slowfade = Fade(0.45, 0.25, 0.25)

style now_playing_frame is default:
    background "#000000B0"
    xpadding 12
    ypadding 6
    xalign 0.5
    yalign 0.02
    xminimum 260

style now_playing_text is default:
    color "#FFFFFF"
    size 14
    bold True
    xalign 0.5

style loading_text is default:
    color "#FFFFFF"
    size 40
    outlines [(2, "#000000", 0, 0)]


# ============================================================
# LOADING SCREEN
# ============================================================
screen loading_screen():
    add "images/bg1.png"
    text "Preparing pages…" style "loading_text" xalign 0.5 yalign 0.5


# ============================================================
# SCREENS
# ============================================================

screen no_rollback():
    $ renpy.block_rollback()

screen jump_to_page():
    modal True
    frame:
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 10
            text "Jump to page:"
            input value VariableInputValue("jump_target")
            textbutton "Go" action Return(jump_target)
            textbutton "Cancel" action Return(None)

screen book_reader(current_text, wc_text, page_text, now_playing_text):

    use no_rollback

    # Navigation keys
    key "K_UP" action Return("next")
    key "mouseup_1" action Return("next")
    key "K_RETURN" action Return("next")
    key "K_SPACE" action Return("next")

    key "K_DOWN" action Return("back")
    key "K_PAGEDOWN" action Return("back")

    key "K_PAGEUP" action Return("next")

    key "K_HOME" action Return("home")
    key "K_END" action Return("end")

    key "K_LEFT" action Return("skip5")
    key "K_RIGHT" action Return("skip5fwd")

    key "j" action Return("jump")
    key "b" action Return("bookmark")
    key "g" action Return("goto_bookmark")

    key "m" action Return("music_menu")

    # Font size
    key "K_PLUS" action SetVariable("reader_font_size", reader_font_size + 2)
    key "K_KP_PLUS" action SetVariable("reader_font_size", reader_font_size + 2)
    key "K_MINUS" action SetVariable("reader_font_size", max(10, reader_font_size - 2))
    key "K_KP_MINUS" action SetVariable("reader_font_size", max(10, reader_font_size - 2))

    # Now Playing
    frame:
        style "now_playing_frame"
        if now_playing_text:
            text now_playing_text style "now_playing_text"
        else:
            text " " size 1

    # Main reading frame
    frame:
        background "#00000080"
        xpos 110
        ypos 110
        xsize 1700
        ysize 860
        xpadding 40
        ypadding 30

        text current_text:
            size reader_font_size
            line_spacing 6
            color "#ffffff"

    # Bottom info bar
    hbox:
        xpos 110
        ypos 990
        xsize 1700
        xfill True
        spacing 20

        text wc_text size 12 color "#cccccc" xalign 0.0

        text page_text size 14 color "#ffffff" xalign 0.5

        null


# ============================================================
# TRACK SELECTOR
# ============================================================
screen track_selector():

    modal True
    frame:
        xalign 0.5
        yalign 0.5
        padding (40, 40, 40, 40)

        vbox:
            spacing 20
            text "Select Music Track" size 32 xalign 0.5

            hbox:
                spacing 40

                vbox:
                    spacing 10
                    for i in range(1, 11):
                        textbutton "OST {}".format(i):
                            action [
                                SetVariable("current_track", i),
                                Play("music", "audio/ost{}.mp3".format(i), loop=True),
                                Return()
                            ]

                vbox:
                    spacing 10
                    for i in range(11, 21):
                        textbutton "OST {}".format(i):
                            action [
                                SetVariable("current_track", i),
                                Play("music", "audio/ost{}.mp3".format(i), loop=True),
                                Return()
                            ]

            textbutton "Close" action Return() xalign 0.5


# ============================================================
# MAIN LOOP WITH PRELOADING
# ============================================================

label start:

    # Show loading screen
    show screen loading_screen

    # Preload all pages
    $ all_pages = paginate_file("NVL-2-VN.txt", max_lines=34)
    $ total_pages = len(all_pages)

    # Compute total words
    $ total_words = sum(count_words(p) for p in all_pages)

    # Start playlist
    if playlist:
        $ renpy.music.play(playlist, channel="music", loop=True, fadein=1.0)
        $ current_track = 1

    # Initial background
    if backgrounds:
        $ current_bg_index = 0
        scene expression backgrounds[current_bg_index]
    else:
        scene black

    # Remove loading screen
    hide screen loading_screen

    # Start on page 1
    $ page_num = 1
    $ current_text = all_pages[0]

    jump show_page


label show_page:

    # Word count + time
    $ words_read = sum(count_words(p) for p in all_pages[:page_num])
    $ remaining_words = max(0, total_words - words_read)
    $ est_minutes = int(math.ceil(remaining_words / float(wpm))) if wpm > 0 else 0
    $ wc_text = "Words read: {} / {} • Est time left: {} min".format(words_read, total_words, est_minutes)

    # Page X of Y
    $ page_text = "- Page {} of {} -".format(page_num, total_pages)

    # Now Playing
    if current_track > 0:
        $ now_playing_text = "Now Playing: OST {}".format(current_track)
    else:
        $ now_playing_text = ""

    $ result = renpy.call_screen(
        "book_reader",
        current_text=current_text,
        wc_text=wc_text,
        page_text=page_text,
        now_playing_text=now_playing_text
    )

    # NEXT PAGE
    if result == "next":
        if page_num < total_pages:
            $ page_num += 1
            $ current_text = all_pages[page_num - 1]

            # Fade only if background changes
            if backgrounds:
                $ new_bg = ((page_num - 1) // 10) % len(backgrounds)
                if new_bg != current_bg_index:
                    $ current_bg_index = new_bg
                    scene expression backgrounds[current_bg_index] with slowfade
                else:
                    scene expression backgrounds[current_bg_index]

        jump show_page

    # BACK PAGE
    if result == "back":
        if page_num > 1:
            $ page_num -= 1
            $ current_text = all_pages[page_num - 1]

            if backgrounds:
                $ new_bg = ((page_num - 1) // 10) % len(backgrounds)
                if new_bg != current_bg_index:
                    $ current_bg_index = new_bg
                    scene expression backgrounds[current_bg_index] with slowfade
                else:
                    scene expression backgrounds[current_bg_index]

        jump show_page

    # SKIP 5 BACK
    if result == "skip5":
        $ page_num = max(1, page_num - 5)
        $ current_text = all_pages[page_num - 1]
        jump show_page

    # SKIP 5 FORWARD
    if result == "skip5fwd":
        $ page_num = min(total_pages, page_num + 5)
        $ current_text = all_pages[page_num - 1]
        jump show_page

    # BOOKMARK
    if result == "bookmark":
        $ bookmark_page = page_num
        jump show_page

    # GO TO BOOKMARK
    if result == "goto_bookmark":
        if bookmark_page:
            $ page_num = bookmark_page
            $ current_text = all_pages[page_num - 1]
        jump show_page

    # MUSIC MENU
    if result == "music_menu":
        $ renpy.call_screen("track_selector")
        jump show_page

    # JUMP TO PAGE
    if result == "jump":
        $ jump_target = ""
        $ target = renpy.call_screen("jump_to_page")
        if target:
            $ page_num = max(1, min(total_pages, int(target)))
            $ current_text = all_pages[page_num - 1]
        jump show_page

    # HOME
    if result == "home":
        $ page_num = 1
        $ current_text = all_pages[0]
        jump show_page

    # END
    if result == "end":
        $ page_num = total_pages
        $ current_text = all_pages[-1]
        jump show_page


label end_of_book:
    "The end."
    return

