import os
import sys
os.environ["KIVY_NO_ARGS"] = "1"
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.clock import ClockBaseBehavior
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.animation import Animation
from kivy.uix.behaviors import ToggleButtonBehavior

import argparse
from datetime import datetime, timedelta
from functools import partial
import cv2
import threading

Builder.load_file('gui_test_kivy.kv')

def parse_args_inferrence():
    """Parse input arguments."""
    type_list = lambda x:list(map(int, x.split(',')))
    parser = argparse.ArgumentParser(description='Trt_inferrence.')
    parser.add_argument('--config_path', default = '../config/connective_tissue_deeplab_v3plus.yaml', type=str, help='Path to the config file.')
    parser.add_argument('--input', default= 'CustomVideo.mp4', type=str, help='Path to the video to process.')
    parser.add_argument('--input_size', default = [1080, 1920], type=type_list, help='window_width')
    parser.add_argument('--trt_model1', default = 'Trt/Onnx2Trt/Trt_Models/laddernet/laddernet_1072_1920.engine', type=str, help='Path to trt_model1.')
    parser.add_argument('--trt_model2', default = 'Trt/Onnx2Trt/Trt_Models/deeplab_origi/deeplab_origi_1072_1920.engine', type=str, help='Path to trt_model1.')
    parser.add_argument('--crop_size', default = [1072, 1920], type=type_list, help='window_width')
    parser.add_argument('--model_input_size', default = [1072, 1920], type=type_list, help='window_width')
    parser.add_argument('--window_size', default = [960, 1280], type=type_list, help='window_width')
    parser.add_argument('--mode', default = 'video', type=str, help='input_data[video or capture')
    parser.add_argument('--style', type=str, default="softmap_torch", help='Path to the config file.')
    parser.add_argument('--label', type=str, default=None, help='specify the label to visualize.')
    parser.add_argument('-t', '--thresh', type=float, default=None, help='threshold for visulaization.')
    parser.add_argument('--max-opacity', type=float, default=None, help='max opacity for soft-mapping.')
    parser.add_argument('--min-opacity', type=float, default=None, help='min opacity for soft-mapping.')
    parser.add_argument('--time_output', type=str, default=False, help='min opacity for soft-mapping.')
    parser.add_argument('--color', nargs=3, type=int, default=None)
    parser.add_argument('-l', '--loop', action='store_true')
    args = parser.parse_args()
    return args

# class TrtInferrenceWidget(BoxLayout):
# class TrtInferrenceWidget(FloatLayout):
class TrtInferrenceWidget(Widget):
    WIND_BASE_X = WIND_BASE_Y = 0
    CTRL_BUTTONS_X = 1820

    MODEL_DROPDWN_X = CTRL_BUTTONS_X
    MODEL_DROPDWN_Y = 980
    CONFIG_PANEL_OPEN_X = CTRL_BUTTONS_X
    CONFIG_PANEL_CLOSE_X = 1950
    CONFIG_PANEL_Y = 250
    ON_OFF_BUTTON_X = CTRL_BUTTONS_X
    ON_OFF_BUTTON_Y = 150
    ANAUT_BUTTON_X = CTRL_BUTTONS_X
    ANAUT_BUTTON_Y = 50
    QUIT_BUTTON_X = CTRL_BUTTONS_X
    QUIT_BUTTON_Y = WIND_BASE_Y

    # FPS_LABEL_X = 1750
    FPS_LABEL_X = 1700
    FPS_LABEL_Y = WIND_BASE_Y
    BORDER_HIGHT = 26
    COLOR_FULL_VAL = 255

    # videoTexture = ObjectProperty(None)
    # self.fps_str = StringProperty("default")

    def __init__(self, args, **kwargs):
        super(TrtInferrenceWidget, self).__init__(**kwargs)

        if args.mode == "capture":
            self.video_capture = cv2.VideoCapture(args.input)
            # self.video_capture = get_stream()
        else:
            self.video_capture = cv2.VideoCapture(args.input)

        self.args = args

        if not self.video_capture.isOpened():
            print('open video file failed !!')
            sys.exit(1)
        
        self.width = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.hight = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if args.mode == "capture":
            # self.fps = 60
            # self.total_frame = 0
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.total_frame = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        else:
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.total_frame = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.ideal_timer = 1.0 / self.fps

        print("width = "+str(self.width))
        print("hight = "+str(self.hight))
        print("fps   = "+str(self.fps))
        print("timer = "+str(self.ideal_timer))
        print("total_frame = {}".format(self.total_frame))

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.frame_buf_size = 3     # seconds
        self.buf_max_frames = int(self.fps*self.frame_buf_size)
        print("buf_max_frames = {}".format(self.buf_max_frames))
        self.total_w_index = 0
        self.total_r_index = 0
        self.frame_r_index = 0
        self.frame_buf0 = []
        self.frame_buf1 = []
        self.fbuf_w_index = 0
        self.fbuf_r_index = 0

        self.read_frame_block() #Fill frame_buf0
        self.read_frame_block() #Fill frame_buf1

        self.video = self.ids["video_image"]
        self.fps_label = self.ids["time_stamp"]
        self.on_off_btn = self.ids["on_off_btn"]
        self.timer_off_btn = self.ids["timer_off_btn"]
        self.select_btn = self.ids["select_btn"]
        self.config_panel = self.ids["config"]
        self.dropdown_btn = self.ids["dropdown"]

        # self.videoTexture = Texture.create(size=(self.frame_buf0[0].shape[1], self.frame_buf0[0].shape[0]), colorfmt='bgr')

        self.on_timer_trg = Clock.create_trigger(self.on_timer_cb, self.timer_off_btn.value)
        self.on_timer_trg.cancel()

        self.read_fblock_trg = Clock.create_trigger(self.read_frame_timer)
        self.read_fblock_trg.cancel()

        self.sync_read_fblock_trg = Clock.create_trigger(self.sync_read_frame)
        self.sync_read_fblock_trg.cancel()

        if args.mode == "capture":
            Clock.schedule_once(self.image_update)
        else:
            Clock.schedule_interval(self.image_update, self.ideal_timer)
            # Clock.schedule_once(self.image_update, self.ideal_timer)

        print("Timer = {}".format(self.ideal_timer))
        self.saved_time = datetime.now()
        self.ideal_next_time = None
        self.ptime_mean = 0.0
        self.time_delta_mean = 0
        self.mean_count = 0

    def read_frame_timer(self,dt):
        self.frame_read_trd = threading.Thread(target=self.read_frame_block)
        self.frame_read_trd.start()

    def sync_read_frame(self,dt):
        # print("sync_read_frame started !!")
        self.frame_read_trd.join()
        # print("sync_read_frame completed !!")

    def read_frame_block(self):
        start_time = datetime.now()
        print("{} read_frame_block started !!".format(start_time.time()))
        frame_buf = self.frame_buf1 if self.fbuf_w_index else self.frame_buf0
        frame_buf.clear()

        for index in range( 0, self.buf_max_frames ):
            # self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index+index)
            ret, frame = self.video_capture.read()
            if ret:
                frame_buf.append(frame)
            else:
                if self.args.loop :
                    print("video looped !! index: {}".format(index))
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.video_capture.read()
                    if ret:
                        frame_buf.append(frame)
                    else:
                        index -= 1
                        print("video loop read failed !! wbuf index: {} last w index: {}".format(self.fbuf_w_index, index))
                        break
                else:
                    index -= 1
                    print("video file read completed !! wbuf index: {} last w index: {}".format(self.fbuf_w_index, index))
                    break
        
        if index >= 0:
            self.total_w_index += index + 1
            self.fbuf_w_index = 0 if self.fbuf_w_index else 1
        
        # self.sync_read_fblock_trg()
        delta_time = datetime.now()-start_time
        # print("{}.{} read_frame_block completed !! total_w_index: {} fbuf_w_index: {}".format(delta_time.seconds, delta_time.microseconds, self.total_w_index,self.fbuf_w_index))
        print("{}.{} read_frame_block completed !! delta:{} total_w_index: {} total_r_index: {}".format(delta_time.seconds, delta_time.microseconds, self.total_w_index-self.total_r_index, self.total_w_index,self.total_r_index))

    def image_update(self, dt):
        time_pstart = datetime.now()
        
        MSEC = 1000000
        TD_MEAN_COUNT_MAX = 10

        frame_buf = self.frame_buf1 if self.fbuf_r_index else self.frame_buf0

        frame = frame_buf[self.frame_r_index]
        self.frame_r_index += 1
        self.total_r_index += 1
        if self.frame_r_index >= self.buf_max_frames:
            print("{} Change frame buffer to buff{}. total_w_index: {} buf_max_frames: {} total_r_index: {}".format(time_pstart.time(), (0 if self.fbuf_r_index else 1), self.total_w_index, self.buf_max_frames, self.total_r_index))
            self.read_fblock_trg()
            self.frame_r_index = 0
            self.fbuf_r_index = 0 if self.fbuf_r_index else 1

        # print("frame_r_index: {} fbuf_r_index: {} total_r_index: {}".format(self.frame_r_index, self.fbuf_r_index, self.total_r_index))
        # print("total_w_index:{} total_r_index:{} fbuf_r_index:{} frame_r_index:{} fbuf_w_index:{}".format(self.total_w_index, self.total_r_index, self.fbuf_r_index, self.frame_r_index, self.fbuf_w_index))

        if self.total_w_index > self.total_r_index:
            canvas = cv2.flip(frame, 0)

            video_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            video_texture.blit_buffer(canvas.tostring(), colorfmt='bgr', bufferfmt='ubyte')
            self.video.texture = video_texture
            # self.videoTexture.blit_buffer(canvas.tostring(), colorfmt='bgr', bufferfmt='ubyte')
            # self.video.texture = self.videoTexture

            time_now = datetime.now()
            process_time = time_now - time_pstart
            self.ptime_mean += process_time.seconds + process_time.microseconds/MSEC
            self.ptime_mean /= 2.0
            # print("ptime_mean: {}".format(self.ptime_mean))

            if self.ideal_next_time == None:
                self.ideal_next_time = time_now
                
            self.ideal_next_time += timedelta(microseconds=self.ideal_timer*MSEC)
            if time_now > self.ideal_next_time:
                self.ideal_next_time = time_now + timedelta(microseconds=self.ideal_timer*MSEC)
                delta = time_now - self.ideal_next_time
                if (delta.seconds + delta.microseconds/MSEC) > self.ideal_timer:
                    next_timer = 0
                else:
                    act_time_delta = self.ideal_next_time - time_now
                    next_timer = act_time_delta.seconds + act_time_delta.microseconds/MSEC - self.ptime_mean
            else:
                act_time_delta = self.ideal_next_time - time_now
                next_timer = act_time_delta.seconds + act_time_delta.microseconds/MSEC - self.ptime_mean
            if next_timer < 0:
                next_timer = 0
            # print("ideal_next_time: {} time_now: {} act_time_delta: {}".format(self.ideal_next_time.second+self.ideal_next_time.microsecond/MSEC,\
            #                                                                 time_now.second+time_now.microsecond/MSEC, act_time_delta.seconds+act_time_delta.microseconds/MSEC))
            # print("time_delta.seconds:{} time_delta.microseconds:{}".format(time_delta.seconds,time_delta.microseconds/MSEC))

            time_delta = time_now - self.saved_time
            self.mean_count += 1
            if self.mean_count >= TD_MEAN_COUNT_MAX:
                self.time_delta_mean /= TD_MEAN_COUNT_MAX
                self.mean_count = 0
                # print("mean_count: {} time_delta_mean: {} FPS: {}".format(self.mean_count, self.time_delta_mean, MSEC/self.time_delta_mean))
            else:
                # print("mean_count: {} time_delta_mean: {} time_delta_mean+: {}".format(self.mean_count, self.time_delta_mean, self.time_delta_mean+time_delta.microseconds))
                self.time_delta_mean += time_delta.microseconds
            self.saved_time = time_now
            # if( self.ideal_timer > time_delta.microseconds/MSEC ):
            #     next_timer = self.ideal_timer+(self.ideal_timer-time_delta.microseconds/MSEC)
            # else:
            #     # next_timer = 0.0
            #     next_timer = self.ideal_timer-(time_delta.microseconds/MSEC-self.ideal_timer)
            # print("IDEAL: {:.4f} DELTA: {:.4f} DT: {:.4f} FPS: {:.4f} NEXT: {:.4f}".format(self.ideal_timer, time_delta.microseconds/MSEC, dt, MSEC/time_delta.microseconds, next_timer))

            if self.mean_count == 0:
                # if (self.fps - 3) > MSEC/time_delta.microseconds:
                if (self.fps - 3) > MSEC/self.time_delta_mean:
                    # fps_str = "FPS: [color=ff0000][b]{:.1f}[/b][/color]".format(MSEC/time_delta.microseconds)
                    # self.fps_label.text = "DELTA: {:.4f} FPS: [color=ff0000][b]{:.1f}[/b][/color]".format(time_delta.microseconds/MSEC, MSEC/time_delta.microseconds)
                    self.fps_label.text = "DELTA: {:.4f} FPS: [color=ff0000][b]{:.1f}[/b][/color]".format(self.time_delta_mean/MSEC, MSEC/self.time_delta_mean)
                else:
                    # fps_str = "FPS: {:.1f}".format(MSEC/time_delta.microseconds)
                    # self.fps_label.text = "DELTA: {:.4f} FPS: {:.1f}".format(time_delta.microseconds/MSEC, MSEC/time_delta.microseconds)
                    self.fps_label.text = "DELTA: {:.4f} FPS: {:.1f}".format(self.time_delta_mean/MSEC, MSEC/self.time_delta_mean)

            if self.args.mode == "capture":
                # self.capture_timer()
                Clock.schedule_once(self.image_update, next_timer)
            # else:
            #     Clock.schedule_once(self.image_update, next_timer)
        else:
            print("video data read completed !! total_w_index: {} total_r_index: {}".format(self.total_w_index, self.total_r_index))
            self.on_stop()

    def on_start(self):
        print("TrtInferrenceWidget: on_start called!!")
    
    def on_stop(self):
        print("TrtInferrenceWidget: on_stop called!!")
        self.video_capture.release()
        exit(0)

    def full_screen(self):
        if not Window.fullscreen:
            Window.fullscreen = True
        else:
            Window.fullscreen = False

    def borderless_mode(self):
        if not Window.borderless:
            Window.maximize()
            Window.borderless = True
            self.select_btn.pos = [self.MODEL_DROPDWN_X, self.MODEL_DROPDWN_Y+self.BORDER_HIGHT]
        else:
            Window.borderless = False
            self.select_btn.pos = [self.MODEL_DROPDWN_X, self.MODEL_DROPDWN_Y]

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print("_on_keyboard_down: keycode = {0} text = {1}".format(keycode, text))
        if keycode[1] == "q" or keycode[1] == "escape":
            self.on_stop()
        elif keycode[1] == "f":
            self.full_screen()
        elif keycode[1] == 'b':
            self.borderless_mode()
        return True

    def on_touch_down(self, touch):
        print(touch)
        if touch.button == 'left':
            print("on_touch_down: Left button pressed.!!")
        elif touch.button == 'right':
            print("on_touch_down: Right button pressed.!!")
            dropdown = self.dropdown_btn
            dropdown.open(self)
        elif touch.button == 'middle':
            print("on_touch_down: Middle button pressed.!!")
        return super(TrtInferrenceWidget, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        print(touch)
        if touch.button == 'left':
            print("on_touch_up: Left button released.!!")
        elif touch.button == 'right':
            print("on_touch_up: Right button released.!!")
        elif touch.button == 'middle':
            print("on_touch_up: Middle button released.!!")
        return super(TrtInferrenceWidget, self).on_touch_up(touch)
    
    def on_touch_move(self, touch):
        print(touch)
        return super(TrtInferrenceWidget, self).on_touch_move(touch)

    def slider(self, state):
        # print("slider: state = {}".format(state))
        if state == "down" :
            pos=(self.CONFIG_PANEL_OPEN_X, self.CONFIG_PANEL_Y)
        else:
            pos=(self.CONFIG_PANEL_CLOSE_X, self.CONFIG_PANEL_Y)
        animation = Animation(pos=pos, t='linear', duration=0.3)
        animation.start(self.config_panel)

    def color_ratio(self, color_str):
        rgba = list(color_str.split(","))
        rgba_int = [int(value) for value in rgba]
        color_ratio = [int(value)/self.COLOR_FULL_VAL for value in rgba]
        # print("RGBA: {0} RATIO: {1}".format(rgba_int, color_ratio))
        return color_ratio

    def rgba_color(self, color_str):
        rgba = list(color_str.split(","))
        rgba_int = [int(value) for value in rgba]
        # print("RGBA: {0}".format(rgba_int))
        return rgba_int

    def mode_btn_ctrl(self, text):
        w_list = ToggleButtonBehavior.get_widgets("sel_model")
        for w in w_list:
            if w.text == text:
                w.state = "down"
            else:
                w.state = "normal"

    def on_off_btn_ctrl(self, state):
        if state == "normal":
            self.timer_off_btn.disabled = True
            self.timer_off_btn.state = "normal"
        else:
            self.timer_off_btn.disabled = False
            self.on_timer_trg.cancel()

    def set_on_timer(self, timeout, state):
        if state == "normal":
            self.timer_off_btn.state = "down"
        else:
            self.on_off_btn.state = "normal"; 
            self.on_timer_trg()

    def on_timer_cb(self, dt):
        if self.timer_off_btn.state == "down":
            self.on_off_btn.state = "down"
            self.timer_off_btn.state = "normal"
    
class TrtInferrenceApp(App):
    def __init__(self, **kwargs):
        super(TrtInferrenceApp, self).__init__(**kwargs)

        # Window.minimum_height = 600
        # Window.minimum_width = 800
        print("Window.minimum_height:{0} Window.minimum_width:{1}".format(str(Window.minimum_height) ,str(Window.minimum_width)))

        # Window.fullscreen = True
        # Window.maximize()
        Config.set("input", "mouse", "mouse,multitouch_on_demand") #Disable multi touch emulation

        self.args = parse_args_inferrence()
        print(self.args)

    def build(self):
        Window.bind(mouse_pos=self.pointer_pos)
        self.trtInferrenceWidget = TrtInferrenceWidget(self.args)
        return self.trtInferrenceWidget
    
    def on_start(self):
        print("TrtInferrenceApp: on_start !!")

    def on_stop(self):
        print("TrtInferrenceApp: on_stop !!")
        exit(0)
    
    def pointer_pos(self, win, p):
        pass
        # print("Mouse Position: {}".format(str(p)))
    
if __name__ == "__main__":
    TrtInferrenceApp().run()
