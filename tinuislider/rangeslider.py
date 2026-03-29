from typing import Literal

from tinui import BasicTinUI
from tinui.TinUI import TinUIString


class RangeSlider:
    """
    双端滑动条
    """

    def __init__(
        self,
        canvas: BasicTinUI,
        pos: tuple,
        width=200,
        fg="#4554dc",
        activefg="#4554dc",
        bg="#868686",
        buttonbg="#ffffff",
        buttonoutline="#cccccc",
        data=(1, 2, 3, 4, 5),
        start_left=None,
        start_right=None,
        direction:Literal["x", "y"]="x",
        anchor="nw",
        command=None,
    ):
        self.canvas = canvas
        self.pos = list(pos)
        self.width = width
        self.fg = fg
        self.activefg = activefg
        self.bg = bg
        self.buttonbg = buttonbg
        self.buttonoutline = buttonoutline
        self.data = list(data)
        self.direction = direction
        self.anchor = anchor
        self.command = command
        self.scale_value = canvas.scale_value

        # 初始索引
        self.left_index = 0 if start_left is None else start_left
        self.right_index = len(self.data) - 1 if start_right is None else start_right

        self.dash = []
        self.uid = None
        self.back = None
        self.active = None

        self.left_button = None
        self.right_button = None
        self.left_fore = None
        self.right_fore = None

        self.startpos = 0

        self._init_items()
        self._calc_dash()
        self._bind_events()
        self._apply_layout()

        self._update_buttons()
        self._update_active()

    def _init_items(self):
        half = self.width / 2
        if self.direction == "x":
            back_coords = (
                self.pos[0] - half, self.pos[1] + self.scale_value(8),
                self.pos[0] + half, self.pos[1] + self.scale_value(8),
            )
        elif self.direction == "y":
            back_coords = (
                self.pos[0] + self.scale_value(8), self.pos[1] + half,
                self.pos[0] + self.scale_value(8), self.pos[1] - half,
            )
        else:
            raise ValueError("direction must be 'x' or 'y'")

        self.back = self.canvas.create_line(
            back_coords,
            fill=self.bg, width=self.scale_value(3,True), capstyle="round"
        )
        self.uid = TinUIString(f"rangeslider-{self.back}")
        self.uid.layout = self.__layout
        self.canvas.itemconfig(self.back, tags=self.uid)

    def _calc_dash(self):
        step = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
        half = self.width / 2

        self.dash.clear()
        if self.direction == "x":
            start = self.pos[0] - half
            for _ in self.data:
                self.dash.append(start)
                start += step
        else:
            start = self.pos[1] + half
            for _ in self.data:
                self.dash.append(start)
                start -= step

    def _create_button(self, pos, tag):
        tags = (self.uid, tag)
        button_pos = (pos + self.scale_value(8), self.pos[1] + self.scale_value(8)) if self.direction == "x" else (self.pos[0] + self.scale_value(8), pos + self.scale_value(8))

        self.canvas.create_text(button_pos,
            text="\uf127", font="{Segoe Fluent Icons} 12",
            fill=self.buttonbg, tags=tags)

        self.canvas.create_text(button_pos,
            text="\uecca", font="{Segoe Fluent Icons} 12",
            fill=self.buttonoutline, tags=tags)

        fore = self.canvas.create_text(button_pos,
            text="\ue915", font="{Segoe Fluent Icons} 12",
            fill=self.fg, tags=tags)

        return fore

    def _bind_events(self):
        # 高亮区间
        lpos = self.dash[self.left_index]
        rpos = self.dash[self.right_index]

        if self.direction == "x":
            active_coords = (lpos, self.pos[1] + self.scale_value(8), rpos, self.pos[1] + self.scale_value(8))
        else:
            active_coords = (self.pos[0] + self.scale_value(8), lpos, self.pos[0] + self.scale_value(8), rpos)

        self.active = self.canvas.create_line(
            active_coords,
            fill=self.fg, width=self.scale_value(3,True), capstyle="round",
            tags=self.uid
        )
        
        self.left_button = f"left_btn-{self.back}"
        self.right_button = f"right_btn-{self.back}"

        self.left_fore = self._create_button(lpos, self.left_button)
        self.right_fore = self._create_button(rpos, self.right_button)

        # 绑定拖拽
        self.canvas.tag_bind(self.left_button, "<Button-1>", self._mousedown)
        self.canvas.tag_bind(self.right_button, "<Button-1>", self._mousedown)
        self.canvas.tag_bind(self.left_button, "<B1-Motion>", self._drag_left)
        self.canvas.tag_bind(self.right_button, "<B1-Motion>", self._drag_right)
        self.canvas.tag_bind(self.left_button, "<ButtonRelease-1>", self._release_left)
        self.canvas.tag_bind(self.right_button, "<ButtonRelease-1>", self._release_right)

        self.canvas.tag_bind(self.back, "<Button-1>", self._click_track)
        self.canvas.tag_bind(self.active, "<Button-1>", self._click_track)

    def __layout(self, x1, y1, x2, y2, expand=False):
        if not expand:
            dx, dy = self.canvas._BasicTinUI__auto_layout(self.uid, (x1, y1, x2, y2), self.anchor)
            self.pos[0] += dx
            self.pos[1] += dy
            self._rewrite_dash(dx, dy)
        else:
            dx, dy = self.canvas._BasicTinUI__auto_layout(self.uid, (x1, y1, x2, y2), "center")
            self.pos[0] += dx
            self.pos[1] += dy

            self.dash.clear()
            if self.direction == "x":
                self.width = x2 - x1
                step = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
                pos = x1
                self.dash.append(pos)
                for _ in self.data[1:]:
                    pos += step
                    self.dash.append(pos)
            else:
                self.width = y2 - y1
                step = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
                pos = y2
                self.dash.append(pos)
                for _ in self.data[1:]:
                    pos -= step
                    self.dash.append(pos)

            self._rewrite_dash(0, 0, re_dash=False)

    def _rewrite_dash(self, dx, dy, re_dash=True):
        if re_dash:
            for i in range(len(self.dash)):
                if self.direction == "x":
                    self.dash[i] += dx
                else:
                    self.dash[i] += dy

        half = self.width / 2
        if self.direction == "x":
            self.canvas.coords(
                self.back,
                self.pos[0] - half, self.pos[1] + self.scale_value(8),
                self.pos[0] + half, self.pos[1] + self.scale_value(8),
            )
        else:
            self.canvas.coords(
                self.back,
                self.pos[0] + self.scale_value(8), self.pos[1] + half,
                self.pos[0] + self.scale_value(8), self.pos[1] - half,
            )

        self._update_buttons()
        self._update_active()

    def _mousedown(self, event):
        self.startpos = self._event_pos(event)

    def _drag_left(self, event):
        pos = self._event_pos(event)
        right_limit = self._get_button_pos(self.right_button)

        if self.direction == "x":
            pos = min(pos, right_limit)
            pos = max(pos, self.dash[0])  # 不超过最左边界
        else:
            pos = max(pos, right_limit)
            pos = min(pos, self.dash[0])  # 不超过最下边界
        self._move_button(self.left_button, pos)

    def _drag_right(self, event):
        pos = self._event_pos(event)
        left_limit = self._get_button_pos(self.left_button)

        if self.direction == "x":
            pos = max(pos, left_limit)
            pos = min(pos, self.dash[-1])  # 不超过最右边界
        else:
            pos = min(pos, left_limit)
            pos = max(pos, self.dash[-1])  # 不超过最上边界
        self._move_button(self.right_button, pos)

    def _release_left(self, _):
        self.canvas.tag_raise(self.left_button, self.right_button)
        self.left_index = self._snap(self.left_button)
        self.left_index = min(self.left_index, self.right_index)
        self._update_buttons()
        self._update_active()
        self._send()

    def _release_right(self, _):
        self.canvas.tag_raise(self.right_button, self.left_button)
        self.right_index = self._snap(self.right_button)
        self.right_index = max(self.right_index, self.left_index)
        self._update_buttons()
        self._update_active()
        self._send()

    def _click_track(self, event):
        pos = self._event_pos(event)

        left_pos = self._get_button_pos(self.left_button)
        right_pos = self._get_button_pos(self.right_button)

        if abs(pos - left_pos) <= abs(pos - right_pos):
            if self.direction == "x":
                pos = min(pos, right_pos)
            else:
                pos = max(pos, right_pos)
            self._move_button(self.left_button, pos)
            self._release_left(None)
        else:
            if self.direction == "x":
                pos = max(pos, left_pos)
            else:
                pos = min(pos, left_pos)
            self._move_button(self.right_button, pos)
            self._release_right(None)

    def _get_button_pos(self, tag):
        coords = self.canvas.coords(tag)
        return coords[0] if self.direction == "x" else coords[1]

    def _event_pos(self, event):
        return self.canvas.canvasx(event.x) if self.direction == "x" else self.canvas.canvasy(event.y)

    def _move_button(self, tag, target_x):
        curr = self._get_button_pos(tag)
        if self.direction == "x":
            self.canvas.move(tag, target_x - curr, 0)
        else:
            self.canvas.move(tag, 0, target_x - curr)
        self._update_active()

    def _snap(self, tag):
        pos = self._get_button_pos(tag)
        nearest = min(self.dash, key=lambda d: abs(d - pos))
        return self.dash.index(nearest)

    def _update_buttons(self):
        l = self.dash[self.left_index]
        r = self.dash[self.right_index]

        self._move_button(self.left_button, l)
        self._move_button(self.right_button, r)

    def _update_active(self):
        l = self._get_button_pos(self.left_button)
        r = self._get_button_pos(self.right_button)

        if self.direction == "x":
            self.canvas.coords(self.active, l, self.pos[1] + self.scale_value(8), r, self.pos[1] + self.scale_value(8))
        else:
            self.canvas.coords(self.active, self.pos[0] + self.scale_value(8), l, self.pos[0] + self.scale_value(8), r)

    def _send(self):
        if self.command:
            self.command(self.get())
    
    def _apply_layout(self):
        dx, dy = self.canvas._BasicTinUI__auto_anchor(self.uid, self.pos, self.anchor)
        self.pos[0] += dx
        self.pos[1] += dy
        self._rewrite_dash(dx, dy)

    # ========== API ==========
    def disable(self, sign="#C8C8C8"):
        self.canvas.itemconfig(self.left_fore, state='disabled', fill=sign)
        self.canvas.itemconfig(self.right_fore, state='disabled', fill=sign)
        self.canvas.itemconfig(self.active, state='disabled', fill=sign)
        self.canvas.itemconfig(self.back, state='disabled')
        self.canvas.itemconfig(self.uid, state='disabled')
    
    def active_state(self):
        self.canvas.itemconfig(self.left_fore, state='normal', fill=self.fg)
        self.canvas.itemconfig(self.right_fore, state='normal', fill=self.fg)
        self.canvas.itemconfig(self.active, state='normal', fill=self.fg)
        self.canvas.itemconfig(self.back, state='normal')
        self.canvas.itemconfig(self.uid, state='normal')

    def get(self):
        return self.data[self.left_index], self.data[self.right_index]

    def set(self, left=None, right=None):
        """设置选中范围值"""
        if left in self.data:
            self.left_index = self.data.index(left)
        if right in self.data:
            self.right_index = self.data.index(right)
        self._update_buttons()
        self._update_active()


if __name__ == "__main__":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(2) # 高DPI适配
    scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
    from tkinter import Tk
    from tinui import ExpandPanel, VerticalPanel
    def on_resize(event):
        rp.update_layout(10,10,event.width-10,event.height-10)
    def on_change(val):
        print("Range:", val)

    root = Tk()
    root.geometry("400x200")

    ui = BasicTinUI(root)
    ui.set_scale(scale_factor)
    ui.pack(fill="both", expand=True)

    slider = RangeSlider(
        canvas=ui,
        pos=(100, 100),
        width=250,
        data=list(range(0, 101, 10)),
        start_left=2,
        start_right=7,
        anchor="center",
        direction='y',
        command=on_change,
    )

    rp = ExpandPanel(ui)
    vp = VerticalPanel(ui)
    rp.set_child(vp)

    ep1 = ExpandPanel(ui)
    vp.add_child(ep1, weight=1)
    ep1.set_child(slider.uid)

    ui.bind("<Configure>", on_resize)

    root.mainloop()