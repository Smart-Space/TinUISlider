from typing import Literal

from tinui import BasicTinUI
from tinui.TinUI import TinUIString

class CenterSlider:
    """
    中心起点双向滑块控件
    基于 BasicTinUI 的 add_scalebar 逻辑重构，以 pos 为中心，向两侧延伸
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
        start=None, # 默认为中间索引
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
        self.data = data
        self.direction = direction
        self.anchor = anchor
        self.command = command
        self.scale_value = canvas.scale_value
        
        self.nowselect = 0
        if start is None:
            self.nowselect = len(data) // 2 # 默认中间
        else:
            self.nowselect = start

        self.dash = [] # 刻度位置列表
        self.uid = None
        self.back = None
        self.active = None
        self.button = None
        self.button_fore = None
        
        # 记录拖拽起始位置
        self.startpos = 0
        
        self._init_items()
        self._calc_dash()
        self._bind_events()
        self._apply_layout()
        
        # 初始化选中状态
        self.select(self.nowselect, send=False)

    def _init_items(self):
        """创建基础图形元素"""
        half_width = self.width / 2
        # 计算背景线坐标
        if self.direction == "x":
            back_coords = (self.pos[0] - half_width, self.pos[1] + self.scale_value(8), 
                           self.pos[0] + half_width, self.pos[1] + self.scale_value(8))
        elif self.direction == "y":
            back_coords = (self.pos[0] + self.scale_value(8), self.pos[1] + half_width, 
                           self.pos[0] + self.scale_value(8), self.pos[1] - half_width)
        else:
            # 仅这一处提醒
            raise ValueError("Direction must be 'x' or 'y'")
            
        self.back = self.canvas.create_line(
            back_coords,
            fill=self.bg,
            width=self.scale_value(3,True),
            capstyle="round",
        )
        
        self.uid = TinUIString(f"centerscale-{self.back}")
        self.uid.layout = self.__layout
        self.canvas.itemconfig(self.back, tags=self.uid)

    def _calc_dash(self):
        """计算刻度位置，以 pos 为中心分布"""
        half_width = self.width / 2
        step = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
        
        self.dash.clear()
        if self.direction == "x":
            start_x = self.pos[0] - half_width
            for _ in self.data:
                self.dash.append(start_x)
                start_x += step
        else:
            start_y = self.pos[1] + half_width
            for _ in self.data:
                self.dash.append(start_y)
                start_y -= step

    def _bind_events(self):
        """绑定事件"""
        init_pos = self.dash[self.nowselect]
        
        self.button = f"scalebutton_center-{self.back}"
        
        btn_tags = (self.uid, self.button)
        button_pos = (init_pos + self.scale_value(8), self.pos[1] + self.scale_value(8)) if self.direction == "x" else (self.pos[0] + self.scale_value(8), init_pos + self.scale_value(8))
        
        self.canvas.create_text(
            button_pos,
            text="\uf127",
            font="{Segoe Fluent Icons} 12",
            fill=self.buttonbg,
            tags=btn_tags,
        )
        self.canvas.create_text(
            button_pos,
            text="\uecca",
            font="{Segoe Fluent Icons} 12",
            fill=self.buttonoutline,
            tags=btn_tags,
        )
        self.button_fore = self.canvas.create_text(
            button_pos,
            text="\ue915",
            font="{Segoe Fluent Icons} 12",
            fill=self.fg,
            tags=btn_tags,
        )
        
        self.canvas.tag_bind(self.button, "<Enter>", lambda _: self.canvas.itemconfig(self.button_fore, fill=self.activefg))
        self.canvas.tag_bind(self.button, "<Leave>", lambda _: self.canvas.itemconfig(self.button_fore, fill=self.fg))
        self.canvas.tag_bind(self.button, "<Button-1>", self._mousedown)
        self.canvas.tag_bind(self.button, "<B1-Motion>", self._drag)
        self.canvas.tag_bind(self.button, "<ButtonRelease-1>", self._check)
        self.canvas.tag_bind(self.back, "<Button-1>", self._checkval)
        
        # 激活线
        if self.direction == "x":
            self.active = self.canvas.create_line(
                (self.pos[0], self.pos[1] + self.scale_value(8), init_pos, self.pos[1] + self.scale_value(8)),
                fill=self.fg,
                width=self.scale_value(3,True),
                tags=self.uid,
                capstyle="round",
            )
        else:
            self.active = self.canvas.create_line(
                (self.pos[0] + self.scale_value(8), self.pos[1], self.pos[0] + self.scale_value(8), init_pos),
                fill=self.fg,
                width=self.scale_value(3,True),
                tags=self.uid,
                capstyle="round",
            )
        self.canvas.tag_bind(self.active, "<Button-1>", self._checkval)
        
        self.canvas.lift(self.button)
    
    def __layout(self, x1, y1, x2, y2, expand=False):
        """面板布局"""
        if not expand:
            dx, dy = self.canvas._BasicTinUI__auto_layout(self.uid, (x1,y1,x2,y2), self.anchor)
            self.pos[0] += dx
            self.pos[1] += dy
            self._rewrite_dash(dx, dy)
        else:
            dx, dy = self.canvas._BasicTinUI__auto_layout(self.uid, (x1,y1,x2,y2), "center")
            self.pos[0] += dx
            self.pos[1] += dy
            self.dash.clear()
            if self.direction == "x":
                self.width = x2 - x1
                dash_t = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
                s = x1
                self.dash.append(s)
                for _ in self.data[1:]:
                    s += dash_t
                    self.dash.append(s)
            else:
                self.width = y2 - y1
                dash_t = self.width / (len(self.data) - 1) if len(self.data) > 1 else 0
                s = y2
                self.dash.append(s)
                for _ in self.data[1:]:
                    s -= dash_t
                    self.dash.append(s)
            self._rewrite_dash(0, 0, False)
            self.select(self.nowselect, send=False)

    def _apply_layout(self):
        dx, dy = self.canvas._BasicTinUI__auto_anchor(self.uid, self.pos, self.anchor)
        self.pos[0] += dx
        self.pos[1] += dy
        self._rewrite_dash(dx, dy)

    def _rewrite_dash(self, dx, dy, re_dash=True):
        """当布局变动时重写刻度位置"""
        if re_dash:
            for i in range(len(self.dash)):
                if self.direction == "x":
                    self.dash[i] += dx
                else:
                    self.dash[i] += dy
        # 更新背景线坐标
        half_width = self.width / 2
        if self.direction == "x":
            self.canvas.coords(self.back, 
                               self.pos[0] - half_width, self.pos[1] + self.scale_value(8), 
                               self.pos[0] + half_width, self.pos[1] + self.scale_value(8))
        else:
            self.canvas.coords(self.back, 
                               self.pos[0] + self.scale_value(8), self.pos[1] + half_width, 
                               self.pos[0] + self.scale_value(8), self.pos[1] - half_width)

    def _mousedown(self, event):
        """鼠标按下"""
        if self.direction == "x":
            self.startpos = self.canvas.canvasx(event.x)
        else:
            self.startpos = self.canvas.canvasy(event.y)
        self.canvas.itemconfig(self.button_fore, text="\ueccc") # 按下状态图标

    def _drag(self, event):
        """拖拽"""
        half_width = self.width / 2
        min_limit = self.pos[0] - half_width if self.direction == "x" else self.pos[1] - half_width
        max_limit = self.pos[0] + half_width if self.direction == "x" else self.pos[1] + half_width
        
        if self.direction == "x":
            current_pos = self.canvas.canvasx(event.x)
            move = current_pos - self.startpos
            if current_pos < min_limit or current_pos > max_limit:
                return
            self.canvas.move(self.button, move, 0)
            # 更新激活线 (从中心 pos[0] 到 current_pos)
            self.canvas.coords(self.active, self.pos[0], self.pos[1] + self.scale_value(8), current_pos, self.pos[1] + self.scale_value(8))
            self.startpos = current_pos
        else:
            current_pos = self.canvas.canvasy(event.y)
            move = current_pos - self.startpos
            if current_pos < min_limit or current_pos > max_limit:
                return
            self.canvas.move(self.button, 0, move)
            self.canvas.coords(self.active, self.pos[0] + self.scale_value(8), self.pos[1], self.pos[0] + self.scale_value(8), current_pos)
            self.startpos = current_pos

    def _check(self, _):
        """鼠标释放，矫正位置"""
        self.canvas.itemconfig(self.button_fore, text="\ue915") # 恢复图标
        bbox = self.canvas.coords(self.button)
        # 获取按钮中心位置
        if self.direction == "x":
            current_val = bbox[0]
            # 限制在范围内
            half_width = self.width / 2
            move = min(max(current_val, self.pos[0] - half_width), self.pos[0] + half_width)
            self.canvas.move(self.button, move - current_val, 0)
        else:
            current_val = bbox[1]
            half_width = self.width / 2
            move = min(max(current_val, self.pos[1] - half_width), self.pos[1] + half_width)
            self.canvas.move(self.button, 0, move - current_val)
            
        # 计算最近的刻度
        rend = min(self.dash, key=lambda x: abs(x - move))
        self.nowselect = self.dash.index(rend)
        
        # 更新激活线到精确刻度
        self.select(self.nowselect, send=True)

    def _checkval(self, event):
        """点击背景条直接跳转"""
        if self.direction == "x":
            move = self.canvas.canvasx(event.x)
            # 更新激活线视觉
            self.canvas.coords(self.active, self.pos[0], self.pos[1] + self.scale_value(8), move, self.pos[1] + self.scale_value(8))
            # 移动按钮
            bbox = self.canvas.coords(self.button)
            self.canvas.move(self.button, move - bbox[0], 0)
        else:
            move = self.canvas.canvasy(event.y)
            self.canvas.coords(self.active, self.pos[0] + self.scale_value(8), self.pos[1], self.pos[0] + self.scale_value(8), move)
            bbox = self.canvas.coords(self.button)
            self.canvas.move(self.button, 0, move - bbox[1])
        self._check(None)

    def select(self, num, send=True):
        """选中某一项"""
        self.nowselect = num
        target_pos = self.dash[num]
        
        # 移动按钮到目标位置
        curr_coords = self.canvas.coords(self.button)
        if self.direction == "x":
            move_x = target_pos - curr_coords[0]
            self.canvas.move(self.button, move_x, 0)
            # 更新激活线
            self.canvas.coords(self.active, self.pos[0], self.pos[1] + self.scale_value(8), target_pos, self.pos[1] + self.scale_value(8))
        else:
            move_y = target_pos - curr_coords[1]
            self.canvas.move(self.button, 0, move_y)
            self.canvas.coords(self.active, self.pos[0] + self.scale_value(8), self.pos[1], self.pos[0] + self.scale_value(8), target_pos)
            
        if self.command and send:
            self.command(self.data[num])

    def disable(self, sign="#C8C8C8"):
        """禁用控件"""
        self.canvas.itemconfig(self.button_fore, state="disable", fill=sign)
        self.canvas.itemconfig(self.back, state="disable")
        self.canvas.itemconfig(self.active, state="disable", fill=sign)
        self.canvas.itemconfig(self.uid, state="disable")

    def active_state(self):
        """激活控件"""
        self.canvas.itemconfig(self.uid, state="normal")
        self.canvas.itemconfig(self.button_fore, state="normal", fill=self.fg)
        self.canvas.itemconfig(self.back, state="normal")
        self.canvas.itemconfig(self.active, state="normal", fill=self.fg)

    def get(self):
        """获取当前选中的值"""
        return self.data[self.nowselect]
    
    def set(self, value):
        """设置选中的值"""
        if value in self.data:
            idx = self.data.index(value)
            self.select(idx)


if __name__ == "__main__":
    # from ctypes import windll
    # windll.shcore.SetProcessDpiAwareness(2) # 高DPI适配
    # scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
    from tkinter import Tk
    from tinui import ExpandPanel, VerticalPanel
    def on_resize(event):
        rp.update_layout(10,10,event.width-10,event.height-10)
    r=Tk()

    ui=BasicTinUI(r)
    # ui.set_scale(scale_factor)
    ui.pack(fill='both',expand=True)

    slider = CenterSlider(
        canvas=ui,
        pos=(0, 100),
        width=200,
        data=range(-10,11),
        start=3, # start是索引，不是值，所以这里是选中数据中的第4项
        anchor="center",
        command=lambda v: print(f"Selected: {v}"),
    )

    # 获取当前值
    val = slider.get()
    print(f"Current value: {val}")
    slider.set(5)  # 设置选中值为 5
    print(f"Value after set: {slider.get()}")

    # 禁用
    # slider.disable()

    rp = ExpandPanel(ui)
    vp = VerticalPanel(ui)
    rp.set_child(vp)

    ep1 = ExpandPanel(ui)
    vp.add_child(ep1, weight=1)
    ep1.set_child(slider.uid)

    ui.bind("<Configure>", on_resize)

    r.mainloop()