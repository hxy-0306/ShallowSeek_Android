import random
import re

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle
    from kivy.metrics import dp
    KIVY_AVAILABLE = True
except ImportError:
    KIVY_AVAILABLE = False

from Q_A import Q_A, BUSY_A, CRAZY_A, ERROR_A

V = "1.3"

last_say = []
is_crazy = False
crazy_n = 0

BG = (0.051, 0.067, 0.090, 1)
COLOR_USER = (0.545, 0.580, 0.620, 1)
COLOR_AI = (0.345, 0.651, 1.000, 1)
COLOR_CRAZY = (0.337, 0.831, 0.863, 1)
COLOR_ERR = (0.973, 0.318, 0.290, 1)
COLOR_DIM = (0.275, 0.298, 0.325, 1)


def _pick_cjk_font():
    candidates = [
        "Noto Sans CJK SC", "Noto Sans CJK", "Noto Sans SC",
        "Droid Sans Fallback", "Droid Sans Chinese", "WenQuanYi Micro Hei",
        "Microsoft YaHei", "SimHei", "PingFang SC", "Heiti SC",
        "Arial Unicode MS",
    ]
    for name in candidates:
        try:
            from kivy.core.text import Label as KivyLabel
            KivyLabel.register(name)
            return name
        except Exception:
            continue
    return None


def clean_float_result(result):
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return (f"{result:.10f}").rstrip('0').rstrip('.')


def pysum(s):
    if len(s) < 41:
        try:
            num = eval(s)
            num = clean_float_result(num)
            return f"答案是：{num}"
        except Exception:
            return "俺不鸡道怎么算w(ﾟДﾟ)w"
    return "算式太长了,俺拒绝计算🤪!"


def become_crazy():
    global is_crazy, crazy_n
    if crazy_n > 9 or random.randint(1, 100) < 11:
        is_crazy = False
        return None
    if is_crazy:
        crazy_n += 1
        group = random.randint(1, 6)
        return random.choice(CRAZY_A[group])
    if random.randint(1, 100) < 6:
        is_crazy = True
        crazy_n += 1
        group = random.randint(1, 6)
        return random.choice(CRAZY_A[group])
    return None


def answer(question):
    global is_crazy
    if "速算" in question or "挑战" in question or "数学" in question:
        return None
    if "石头剪刀布" in question or "猜拳" in question:
        return None
    if "猜数字" in question:
        return None
    if "发疯" in question or "疯狂" in question:
        if not is_crazy:
            is_crazy = True
            return "如你所愿！我要疯了……哇哩哇哩哇！你好！我是疯狂戴夫！"
        return "你说什么?告诉你，我已经疯狂了👾!"
    if "恢复" in question:
        if is_crazy:
            is_crazy = False
            return "好!这就恢复正常👋"
        return "你在说啥?我很正常啊🤔"

    c = become_crazy()
    if c is not None:
        return c

    try:
        q = question.replace("=", "").replace("?", "").replace("!", "")
        q = q.replace(" ", "").replace("？", "").replace("！", "")
        q = q.replace("等于", "").replace("几", "")
    except Exception:
        q = question

    if "刚刚" in q or "之前" in q or "刚才" in q:
        if last_say:
            return f"刚才你问：「{last_say[0]}」，我回答：「{last_say[1]}」"
        return "我们还什么都没聊呢🧐"

    if re.search(r"\d+[+\-*/]\d+", q):
        return pysum(q)

    results = []
    for key in Q_A:
        if re.search(r"^\s*$", q):
            return random.choice(Q_A["not have"])
        if isinstance(Q_A[key], dict):
            if key in q:
                for t in Q_A[key]:
                    if t in q:
                        results.append(random.choice(Q_A[key][t]))
        elif key in q:
            results.append(random.choice(Q_A[key]))

    if not results:
        return random.choice(BUSY_A)
    return "\n".join(results)


# ===== 游戏状态机 =====

def start_rqs():
    return {
        "type": "rqs",
        "c_not_win": 0,
        "p_not_win": 0,
        "done": False,
    }


def step_rqs(state, user_choice):
    valid = ["石头", "剪刀", "布"]
    if user_choice not in valid:
        return ("请出石头、剪刀或布~", False)

    computer = random.choice(valid)
    lines = [f"你出：{user_choice}，我出：{computer}"]

    if computer == user_choice:
        winner = "平局"
        state["c_not_win"] = 0
        state["p_not_win"] = 0
    elif (computer == "布" and user_choice == "石头") or \
         (computer == "石头" and user_choice == "剪刀") or \
         (computer == "剪刀" and user_choice == "布"):
        winner = "我"
        state["p_not_win"] += 1
        state["c_not_win"] = 0
    else:
        winner = "你"
        state["c_not_win"] += 1
        state["p_not_win"] = 0

    if winner == "平局":
        lines.append("本轮平局")
    else:
        lines.append(f"本轮{winner}赢了👍")

    if state["c_not_win"] >= 3:
        lines.append("嘤嘤😥，连输三把，不玩了！")
        state["done"] = True
    elif state["p_not_win"] >= 3:
        lines.append("Sorry，连赢你3把，请不要生气哦😏")
        state["done"] = True

    return ("\n".join(lines), state["done"])


def start_guess_n():
    g_number = random.randint(50, 200)
    s_number = g_number - random.randint(3, 5)
    b_number = g_number + random.randint(3, 5)
    return {
        "type": "guess",
        "g_number": g_number,
        "remaining": 5,
        "hint": f"我想了一个数字，它在 {s_number} 和 {b_number} 之间，你来猜吧！",
        "done": False,
    }


def step_guess_n(state, text):
    if not text.isdigit():
        return ("请输入数字~", False)

    state["remaining"] -= 1
    n = int(text)

    if n == state["g_number"]:
        state["done"] = True
        return (f"猜对了！答案就是 {state['g_number']}！", True)

    if state["remaining"] == 0:
        state["done"] = True
        return (f"机会用完了，正确答案是 {state['g_number']}，游戏结束！", True)

    return (f"不对哦，还有 {state['remaining']} 次机会。再猜：", False)


def start_math():
    import time
    expr, answer = _make_expr()
    return {
        "type": "math",
        "right": 0,
        "min_time": 20,
        "spent_list": [],
        "a_list": [],
        "expr": expr,
        "answer": answer,
        "start_ts": time.time(),
        "done": False,
    }


def _make_expr():
    ops = ["+", "-", "*", "/"]
    while True:
        t = f"{random.randint(2, 20)}{random.choice(ops)}{random.randint(2, 20)}"
        a = eval(t)
        if "-" not in str(a) and "." not in str(a):
            return t, a


def step_math(state, text):
    import time
    spend = int(time.time() - state["start_ts"])
    state["spent_list"].append(spend)
    state["a_list"].append(text)

    if spend < state["min_time"]:
        state["min_time"] = spend

    if spend > 10:
        state["done"] = True
        lines = [f"哦哦，你用了{spend}秒，超时啦！"]
        lines.append(f"这场挑战，你答对了{state['right']}道题。")
        lines.append(f"你最快的一次，只用了{state['min_time']}秒。")
        lines.append("恭喜你！勇士！")
        return ("\n".join(lines), True)

    if text == "n":
        state["done"] = True
        lines = ["好吧，这题你不会，进入结算："]
        lines.append(f"这场挑战，你答对了{state['right']}道题。")
        lines.append(f"你最快的一次，只用了{state['min_time']}秒。")
        lines.append("恭喜你！勇士！")
        return ("\n".join(lines), True)

    try:
        n = int(text)
    except ValueError:
        state["done"] = True
        return ("有违规字符，犯规了！游戏结束", True)

    if n == state["answer"]:
        state["right"] += 1
        state["expr"], state["answer"] = _make_expr()
        state["start_ts"] = time.time()
        return (f"答对啦！下一题👍\n算式 '{state['expr']}=?' 的结果：", False)
    else:
        state["done"] = True
        lines = ["不好！你答错啦！游戏结束👋"]
        lines.append(f"这场挑战，你答对了{state['right']}道题。")
        lines.append(f"你最快的一次，只用了{state['min_time']}秒。")
        lines.append("恭喜你！勇士！")
        return ("\n".join(lines), True)


def get_game_prompt(state):
    if state is None:
        return "说点什么..."
    t = state["type"]
    if t == "rqs":
        return "你出石头、剪刀还是布？"
    if t == "guess":
        return f"猜数字（剩{state['remaining']}次）:"
    if t == "math":
        if state["expr"]:
            return f"{state['expr']}=?"
        return "准备好速算了吗？"
    return "说点什么..."


def step_game(state, text):
    t = state["type"]
    if t == "rqs":
        return step_rqs(state, text)
    if t == "guess":
        return step_guess_n(state, text)
    if t == "math":
        return step_math(state, text)
    return ("", True)


# ===== UI =====

if KIVY_AVAILABLE:
    Window.clearcolor = BG
    CJK_FONT = _pick_cjk_font()

    class ChatBubble(Label):
        def __init__(self, bubble_color=COLOR_AI, **kwargs):
            super().__init__(**kwargs)
            self.color = bubble_color
            self.markup = True
            self.font_size = dp(15)
            self.size_hint_y = None
            self.bind(text=self._recalc)
            if CJK_FONT:
                self.font_name = CJK_FONT

        def _recalc(self, *_):
            self.text_size = (self.width, None)
            self.height = max(dp(24), self.texture_size[1] + dp(8))

        def on_size(self, *a):
            self.text_size = (self.width, None)
            self.height = max(dp(24), self.texture_size[1] + dp(8))

    class ThinkingBar(Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.color = COLOR_DIM
            self.font_size = dp(13)
            self.size_hint_y = None
            self.height = dp(20)
            self._i = 0
            self._dots = ""
            self._event = None
            if CJK_FONT:
                self.font_name = CJK_FONT

        def start(self):
            self._i = 0
            self._dots = ""
            self.text = "🤖 正在思考中"
            self._event = Clock.schedule_interval(self._tick, 0.3)

        def stop(self):
            if self._event:
                self._event.cancel()
                self._event = None
            self.text = ""

        def _tick(self, dt):
            self._i += 1
            if self._i > 5:
                self.stop()
                return
            self._dots += "."
            if len(self._dots) > 3:
                self._dots = "."
            self.text = f"🤖 正在思考中{self._dots}"

    class ShallowSeekApp(App):
        title = "ShallowSeek"

        def build(self):
            self.game_state = None
            self._typing = False
            self._typing_buf = ""

            root = BoxLayout(orientation="vertical", padding=dp(0), spacing=dp(0))

            title_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), padding=[dp(12), dp(0)])
            with title_bar.canvas.before:
                Color(0.078, 0.094, 0.133, 1)
                title_bar._rect = Rectangle(size=title_bar.size, pos=title_bar.pos)
                title_bar.bind(size=lambda w, s: setattr(w._rect, 'size', s),
                               pos=lambda w, p: setattr(w._rect, 'pos', p))
            title_label = Label(
                text=f"ShallowSeek  v{V}",
                size_hint_x=1,
                color=(0.345, 0.651, 1.000, 1),
                font_size=dp(17),
                bold=True,
            )
            if CJK_FONT:
                title_label.font_name = CJK_FONT
            title_bar.add_widget(title_label)
            root.add_widget(title_bar)

            self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4),
                                     scroll_type=['bars', 'content'], do_scroll_x=False)
            self.msg_box = BoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(10), dp(6)], spacing=dp(4))
            self.msg_box.bind(minimum_height=self.msg_box.setter('height'))
            self.scroll.add_widget(self.msg_box)
            root.add_widget(self.scroll)

            self.thinking = ThinkingBar()
            root.add_widget(self.thinking)

            input_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
                                  padding=[dp(8), dp(4)], spacing=dp(6))
            with input_bar.canvas.before:
                Color(0.078, 0.094, 0.133, 1)
                input_bar._rect = Rectangle(size=input_bar.size, pos=input_bar.pos)
                input_bar.bind(size=lambda w, s: setattr(w._rect, 'size', s),
                               pos=lambda w, p: setattr(w._rect, 'pos', p))

            self.input = TextInput(
                hint_text="说点什么...",
                hint_text_color=COLOR_DIM,
                multiline=False,
                size_hint_x=1,
                font_size=dp(15),
                write_tab=False,
            )
            if CJK_FONT:
                self.input.font_name = CJK_FONT
            self.input.bind(on_text_validate=self.on_send)
            input_bar.add_widget(self.input)

            send_btn = Button(text="发送", size_hint_x=None, width=dp(64),
                              font_size=dp(14), background_color=(0.345, 0.651, 1.000, 1),
                              background_normal='', color=(1, 1, 1, 1))
            if CJK_FONT:
                send_btn.font_name = CJK_FONT
            send_btn.bind(on_release=self.on_send)
            input_bar.add_widget(send_btn)

            root.add_widget(input_bar)

            self._add_welcome()
            return root

        def _add_welcome(self):
            self._add_ai("嗨！我是 ShallowSeek(浅度求索)，有什么可以帮你的吗？", instant=True)
            self._add_ai("试试: 你好 / 猜数字 / 石头剪刀布 / 速算 / 发疯 / 1+1=?", instant=True)

        def _add_user(self, text):
            w = ChatBubble(text=f"[color=#8b949e]🧔: {text}[/color]",
                           bubble_color=COLOR_USER)
            self.msg_box.add_widget(w)
            self._scroll_to_bottom()

        def _add_ai(self, text, instant=False, color=None):
            if color is None:
                if is_crazy:
                    color = COLOR_CRAZY
                elif text in ERROR_A:
                    color = COLOR_ERR
                else:
                    color = COLOR_AI

            hex_color = f"{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
            full_markup = f"[color=#{hex_color}]🤖: {text}[/color]"
            plain_body = f"🤖: {text}"

            if instant:
                w = ChatBubble(text=full_markup, bubble_color=color)
                self.msg_box.add_widget(w)
                self._scroll_to_bottom()
                return

            self._typing = True
            self._typing_plain = plain_body
            self._typing_full = full_markup
            self._typing_idx = 0
            w = ChatBubble(text="🤖:", bubble_color=color)
            w.markup = False
            self.msg_box.add_widget(w)
            self._typing_widget = w
            self._scroll_to_bottom()
            Clock.schedule_interval(self._typing_tick, 0.02)

        def _typing_tick(self, dt):
            if not self._typing:
                return False
            self._typing_idx += 1
            if self._typing_idx >= len(self._typing_plain):
                self._typing_widget.text = self._typing_full
                self._typing_widget.markup = True
                self._typing = False
                return False
            self._typing_widget.text = self._typing_plain[:self._typing_idx]
            return True

        def _scroll_to_bottom(self):
            Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.05)

        def on_send(self, *args):
            text = self.input.text.strip()
            if not text or self._typing:
                return
            self.input.text = ""
            self._add_user(text)
            self.thinking.start()
            Clock.schedule_once(lambda dt: self._process(text), 0.5)

        def _process(self, text):
            self.thinking.stop()

            if self.game_state is not None:
                response, done = step_game(self.game_state, text)
                self._add_ai(response)
                if done:
                    self.game_state = None
                return

            result = answer(text)

            if result is None:
                if "速算" in text or "挑战" in text or "数学" in text:
                    self.game_state = start_math()
                    self._add_ai("速算挑战开始！十秒内答题！输入 n 跳过，答错或超时结束。")
                    self._add_ai(f"算式 '{self.game_state['expr']}=?' 的结果：", instant=True)
                elif "石头剪刀布" in text or "猜拳" in text:
                    self.game_state = start_rqs()
                    self._add_ai("石头剪刀布开始！连输/连赢3把结束。你出石头、剪刀还是布？")
                elif "猜数字" in text:
                    self.game_state = start_guess_n()
                    self._add_ai(self.game_state["hint"])
                elif "游戏" in text:
                    if random.randint(0, 1) == 0:
                        self.game_state = start_rqs()
                        self._add_ai("好嘞，石头剪刀布！你出石头、剪刀还是布？")
                    else:
                        self.game_state = start_guess_n()
                        self._add_ai(self.game_state["hint"])
                else:
                    return

                if last_say and last_say[0] != text:
                    last_say.clear()
                    last_say.append(text)
                return

            if result is not None:
                last_say.clear()
                last_say.append(text)
                last_say.append(result)
                self._add_ai(result)

    def run_kivy():
        ShallowSeekApp().run()


def run_cli():
    global is_crazy

    def char_print(text, end=''):
        if not text:
            return
        for ch in text:
            print(ch, end='', flush=True)
            import time
            time.sleep(0.03)
        print(end, end='', flush=True)

    char_print(f"ShallowSeek v{V} 启动完成！输入 h 看帮助\n")
    while True:
        try:
            t = input("🧔: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not t:
            continue
        if t in ("e", "exit", "quit"):
            print("再见啦！")
            break
        if t == "h":
            print("试试: 你好 / 猜数字 / 石头剪刀布 / 速算 / 发疯 / 1+1=? / 恢复")
            continue
        if t == "v":
            print(f"版本号-{V}")
            continue

        result = answer(t)
        if result is None:
            continue
        prefix = "🤖: "
        if is_crazy:
            prefix = "🤖[疯]: "
        elif result in ERROR_A:
            prefix = "🤖[错]: "
        char_print(prefix + result + "\n")


if __name__ == "__main__":
    if KIVY_AVAILABLE:
        run_kivy()
    else:
        print("Kivy 未安装，运行终端模式...")
        print("pip install kivy  可启用 GUI")
        run_cli()
