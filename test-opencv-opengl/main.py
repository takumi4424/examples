#!/usr/bin/env python3

from PyQt5 import QtWidgets, QtCore
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys, platform, cv2, numpy

class GLWidget(QtWidgets.QOpenGLWidget):
    """
    OpenGLに対応するウィジットのクラスを継承し、initializeGL,paintGL,resizeGLをオーバーライドする。
    マウスイベントをキャッチしたければmousePressEventもオーバーライドする。 
    再描画させたいタイミングでself.repaint呼べばおけ。
    """

    def __init__(self, width=800, height=800, parent=None):
        """
        オブジェクト初期化関数
        OpenGLに関する初期化はinitializeGLでやらないと怒られるかも
        """
        # 親クラスのコンストラクタ
        super(GLWidget, self).__init__(parent)

        # 設定保存
        self.width = width
        self.height = height

        # サイズ指定(固定)
        self.setMinimumSize(self.width, self.height)
        # これしないとキーボード入力受け付けてくれん。
        self.grabKeyboard()

        # 経過日数
        self.date = 0
        # 太陽の自転角度
        self.sun_rotation = 0.0
        # 地球の公転角度
        self.earth_revolution = 0.0
        # 地球の自転角度
        self.earth_rotation = 0.0
        # 月の公転角度
        self.moon_revolution = 0.0
        # 月の自転角度
        self.moon_rotation = 0.0

        # 再生/停止フラグ
        self.move = True
        # 視点変更
        self.vp = False

        # 動画保存のための準備。何故か動画が遅くなってたので、60fpsにしてる。
        self.video = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'XVID'), 60.0, (self.width, self.height))

    def initializeGL(self):
        """
        OpenGL初期化的な
        """
        # 背景は黒
        glClearColor(0.0, 0.0, 0.0, 1.0)
        # 奥行き関係を描画する
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        """
        描画時コールバック
        """
        # バッファをクリア(何やってるかわからん)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 射影行列を弄る
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.vp:
            # カメラの画角/アスペクト比/描画する奥行きの範囲を設定
            gluPerspective(50, self.width/self.height, 0.1, 10)

        # モデルビュー行列を弄る
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if self.vp:
            # 視点を設定(実際には座標系を移動させている)
            gluLookAt(0.8,-0.8,1.6, 0.0,0.0,0.0, 0.0,0.0,1.0)
        # 適当に枠作る
        glBegin(GL_LINE_LOOP)
        glColor3d(1.0, 1.0, 1.0)
        glVertex2d(-0.9,-0.9)
        glVertex2d( 0.9,-0.9)
        glVertex2d( 0.9, 0.9)
        glVertex2d(-0.9, 0.9)
        glEnd()
        # まずは太陽を描画
        glPushMatrix()
        glRotated(self.sun_rotation, 0, 0, 1)
        glColor3d(1.0, 0.5, 0.0)
        glutWireSphere(0.2, 12, 8)
        glPopMatrix()
        # ローカル座標系を地球の位置へ(x,y,z軸の方向はワールドと一緒)
        glRotated(self.earth_revolution, 0, 0, 1)
        glTranslated(0.65, 0, 0)
        glRotated(-self.earth_revolution, 0, 0, 1)
        # 地球を描画
        glPushMatrix()
        glRotated(23.43, 0, 1, 0) # 地軸の傾き
        glRotated(self.earth_rotation, 0, 0, 1)
        glColor3d(0.5, 1.0, 0.5)
        glutWireSphere(0.1, 8, 6)
        glPopMatrix()
        # ローカル座標系を月の位置へ(x,y,z軸の方向はワールドと一緒)
        glRotated(self.moon_revolution, 0, 0, 1)
        glTranslated(0.25, 0, 0)
        glRotated(-self.moon_revolution, 0, 0, 1)
        # 月を描画
        glRotated(self.moon_rotation, 0, 0, 1)
        glColor3d(0.2, 0.5, 1.0)
        glutWireSphere(0.08, 8, 6)

        # 一応
        glFlush()

        # 画像保存作業
        # RGBのバイト列としてデータを取得(400×400×3Byte)
        pixels = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
        # 3次元配列に直す
        img = numpy.frombuffer(pixels, dtype=numpy.uint8).reshape(self.width, self.height, 3)
        # OpenGLのRGB形式から、OpenCVのBGR形式に変換
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        # 座標系が上下逆なので、変換
        img = cv2.flip(img, 0)
        # VideoWriteに書き込む
        self.video.write(img)

    def resizeGL(self, width, height):
        """
        ウィンドウリサイズ時のコールバック
        """
        # ウィンドウ全体をビューポートにする
        glViewport(0, 0, width, height)
        # サイズを保存しておく
        self.width = width
        self.height = height

    def mousePressEvent(self, event):
        """
        マウスイベント。
        QtWidgetの関数。
        """
        # 停止 <-> 動作のトグル
        self.move = not self.move

    def keyPressEvent(self, event):
        """
        マウスイベント。
        QtWidgetの関数。
        なぜかself.grabKeyboard()しないとキーボード入力受け付けてくれん。
        """
        # 視点デフォルト <-> 俯瞰的なやつのトグル
        self.vp = not self.vp

    def animate(self):
        """
        これ10回呼び出す毎に1日経過的な。
        公転/自転周期はwikipediaから。
        """
        if self.move:
            # 2.4時間経過
            self.date += 1/10
        # 太陽：自転周期：約27日
        self.sun_rotation = self.date / 27.275 * 360
        # 地球：公転/自転周期：365日/約1日
        self.earth_revolution = self.date / 365 * 360
        self.earth_rotation = self.date / 0.997271 * 360
        # 月：公転/自転周期：約27日/約27日
        self.moon_revolution = self.date / 27.321662 * 360
        self.moon_rotation = self.date / 27.321662 * 360
        # 再描画させる
        self.repaint()

        print('経過日数：', round(self.date), '日', sep='', end='\r')

    def close(self):
        self.video.release()

if __name__ == '__main__':

    if not platform.platform().startswith('Darwin'):
        # Macではなぜか自動でやってくれてるので、それ以外
        glutInit(sys.argv)
    
    # Qtアプリケーションのコントロールなどをするやつ。実際に何やってるかは不明。
    app = QtWidgets.QApplication(sys.argv)

    # パーツを作る(ウィンドウウィジット、OpenGL描画ウィジット、レイアウト)
    window = QtWidgets.QWidget()
    glWidget = GLWidget()
    layout = QtWidgets.QHBoxLayout()
    # 入れ子状に配置してく
    layout.addWidget(glWidget)
    window.setLayout(layout)

    # メッセージ表示
    print("GLWidget上でキーを打つと、視点が[デフォルト<->俯瞰]でトグルします")
    print("GLWidget上でクリックすると、[動作<->停止]でトグルします")

    # アニメーションするためにタイマー使う。
    # Qtから提供されているやつじゃなくてもいいんかな？
    # ひとまず30fps
    timer = QtCore.QTimer()
    timer.timeout.connect(glWidget.animate)
    timer.start(1/30)

    # 表示させてアプリケーションのメインループに入る的な。
    window.show()
    ret = app.exec_()

    # VideoWriteを閉じるための作業
    glWidget.close()

    sys.exit(ret)
