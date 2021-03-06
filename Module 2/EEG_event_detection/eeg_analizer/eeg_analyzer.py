"""
// i n t e r s p e c i f i c s  @  T U B, Autumn 2021
Module 2: Brain Bioelectricity

Potencial de Acción
Python implementations of dynamic time warping DTW algorithm for recognizing eeg events in streamed data.

"""

#0. install dependencies:
#   $ pip install pygame
#   $ pip install numpy
#   $ pip install scipy
#   $ pip install sklearn
#   $ pip install pandas
#   $ pip install dtw
#   $ pip install oscpy

#   -   -   -   -   -   -   -   -
#1. load csv file in main()   
#   -> load_data_csv("./data/EEGdata_02_ReducFilterIC/valery_RF_ELEC.csv")
#2. show electrodes channels
#   -> plots (AF3, AF7, F4, F3, F7, F8)
#3. show dtw distance between training patterns and current streamed data 
#   -> plots (A, B, C, D )
#3. send electrode and dtw signals as OSC, 
#   ->switch on/off, 
#   ->change mode raw/normalized 
#   ->thresholds for dtw channels
#   -   -   -   -   -   -   -   -   


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
import pygame
import pickle, datetime
from oscpy.client import OSCClient
from time import sleep
from glob import glob
from pandas import *
import statistics
import numpy as np 
from sklearn.metrics.pairwise import euclidean_distances
from dtw import accelerated_dtw, dtw
from scipy.stats.stats import pearsonr

dist_fun = euclidean_distances

# colors definition
COLOR_RED =   0xFF00FF
COLOR_GREEN = (255, 255, 0)
COLOR_BLUE =  (0, 255, 255)
COLOR_BG = (255,255,255)
COLORS_ELEC = [
    0xa9d6e5,
    0x89c2d9,
    0x61a5c2,
    0x468faf,
    0x2c7da0,
    0x2a6f97]

COLORS_PATS = [
    0x014f86,
    0x01497c,
    0x013a63,
    0x012a4a
]

# initialize and load font
pygame.init()
W = 720
H = 900
# paths
DATA_PATH = './data'
FONT_PATH = './RevMiniPixel.ttf'
FONT = pygame.font.Font(FONT_PATH, 16)
FONTmini = pygame.font.Font(FONT_PATH, 14)

#   -   -   -   -   -   -   -   change OSC PORT and HOST IP -   -   -   -    -   -  -   -#
OSC_HOST = "192.168.1.250"
OSC_PORT = 9000
OSC_CLIENT = []


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
def pmap(value, inMin, inMax, outMin, outMax):
    """
        Like processing's map function-
        Receives value in range(inMin,inMax)
        Returns a new val in range (outMin, outMax)
    """
    inSpan = inMax - inMin
    outSpan = outMax - outMin
    try:
        transVal = float(value - inMin) / float(inSpan)
        return outMin + (transVal * outSpan)
    except:
        return 0

class Plot():
    """
        Plots are data management and display objects
        Receives position, size, name and color as arguments when creating new objects 
            P = Plot(x, y, w, h, nam, colo) 
        Add new_value to plot 
            P.update(new_value, ch)
        Draw over PLOTS_SCREEN surface in coordinates px,py
            P.draw_h(PLOTS_SCREEN, px, py)
        
    """
    def __init__(self, x, y, w, h, nam, colo):
        # create and update pixel-style plots
        self.pos = []       #position
        self.sz = []        #size
        self.name = nam
        self.color = colo #color
        self.samples = []   #data
        self.samples_fl = []
        self.a = 00         #actual sample
        self.b = 00         #actual mean
        self.n = 256         #number of samples
        self.esta = "[-]"
        # init pos and data
        self.pos = [x,y]
        self.sz =[w, h]
        self.samples = [0.0 for a in range(self.n)]
        self.samples_fl = [0.0 for a in range(self.n)]
        self.font = pygame.font.Font(FONT_PATH, 14)

        return

    def update(self, new_sample, nam):
        # queue new sample and dequeue other data
        self.a = new_sample
        self.samples.append(self.a)
        old = self.samples.pop(0)
        self.esta = nam
        return

    def draw(self, surf, dx, dy):
        # draw the list or create a polygon
        wi = 50
        he = self.n*2
        val_max = max(self.samples)
        val_min = min(self.samples)
        points = [[dx+pmap(s, val_min, val_max, 0, wi), dy+i*2] for i,s in enumerate(self.samples)]
        last_sample = self.samples[-1]
        actual_point = points[-1]
        points = [[dx,dy]] + points + [[dx,dy+(len(self.samples)-1)*2]]
        pygame.draw.polygon(surf, self.color, points, 1)
        pygame.draw.rect(surf, (0,64,0), pygame.Rect(dx,dy,wi,he), 1)
        pygame.draw.line(surf, self.color, (actual_point[0],actual_point[1]-2),(actual_point[0],actual_point[1]+2), 2)
        pygame.draw.line(surf, (0,127,0), (dx,dy+he+29+320),(dx+50,dy+he+29+320), 1)
        pygame.draw.line(surf, (0,255,0), (actual_point[0],actual_point[1]+25+320),(actual_point[0],actual_point[1]+29+320), 2)
        val = self.font.render('W: {:0.2f}'.format(last_sample), 1, self.color)
        surf.blit(val, (dx, 98*2+105+320))
        #n_estacion = self.font.render('< {} >'.format(self.esta), 1, self.color)
        #surf.blit(n_estacion, (dx, dy-20+320))
        return

    def draw_h(self, surf, dx, dy):
        # draw the list or create a polygon
        #wi = self.n*2
        #he = 70
        wi = self.sz[0]
        he = self.sz[1]
        val_max = max(self.samples)
        val_min = min(self.samples)
        points = [[dx+i*2, dy+pmap(s, val_min, val_max, he, 0)] for i,s in enumerate(self.samples)]
        last_sample = self.samples[-1]
        actual_point = points[-1]
        points = [[dx,dy]] + points + [[dx+(len(self.samples)-1)*2, dy]]
        pygame.draw.polygon(surf, self.color, points, 1)
        pygame.draw.rect(surf, (0,64,0), pygame.Rect(dx,dy,wi,he), 1)
        pygame.draw.line(surf, self.color, (actual_point[0]-2,actual_point[1]),(actual_point[0]+2,actual_point[1]), 2)
        pygame.draw.line(surf, (0,127,0), (dx+wi+29+320, dy),(dx+wi+29+320, dy+50), 1)
        pygame.draw.line(surf, (0,255,0), (actual_point[0]+25+320,actual_point[1]),(actual_point[0]+29+320,actual_point[1]), 2)
        val = self.font.render('{}: {:0.2f}'.format(self.name, last_sample), 1, self.color)
        surf.blit(val, (60, dy+50))
        #n_estacion = self.font.render('< {} >'.format(self.esta), 1, self.color)
        #surf.blit(n_estacion, (dx, dy-20+320))
        return


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
WINDOW = pygame.display.set_mode((W, H))

# create surfaces for plots and background
BG_SCREEN = pygame.Surface((W,H))
BG_SCREEN.fill((255,255,255))
PLOTS_SCREEN = pygame.Surface((W,H))

# create buttons for electrodes
N_CHANNELS = 6
CHANNELS = ["AF3", "AF7", "F3", "F4", "F7", "F8"]
LABELS = [FONT.render(cs, 1, (0, 255, 0)) for cs in CHANNELS]
CH_SWITCHES = [pygame.draw.rect(PLOTS_SCREEN, COLOR_GREEN, pygame.Rect(250+320, 50+c*75, 30, 70), 1) for c in range(N_CHANNELS)]
CH_MODES    = [pygame.draw.rect(PLOTS_SCREEN, COLOR_RED, pygame.Rect(285+320,50+c*75, 30, 70), 1) for c in range(N_CHANNELS)]
# create buttons for patterns
N_PATTERNS = 4
PATTERNS = ["A", "B", "C", "D"]
LABELS = [FONT.render(ps, 1, (0, 255, 0)) for ps in PATTERNS]
PM_SWITCHES    = [pygame.draw.rect(PLOTS_SCREEN, COLOR_RED, pygame.Rect(285+320, 550+c*75+35, 70, 30), 1) for c in range(N_PATTERNS)]
PM_MODES    = [pygame.draw.rect(PLOTS_SCREEN, COLOR_RED, pygame.Rect(250+320, 550+c*75, 30, 30), 1) for c in range(N_PATTERNS)]
PM_THRESH = [pygame.draw.rect(PLOTS_SCREEN, COLOR_GREEN, pygame.Rect(285+320, 550+c*75, 30, 30), 1) for c in range(N_PATTERNS)]

# timer events
TIC_EVENT = pygame.USEREVENT + 1
TIC_TIMER = 30
clock = pygame.time.Clock()
running = True

# initialize values for interface
sws = [True for c in range(N_CHANNELS)]
modes = [1  for c in range(N_CHANNELS)] # mode 0 is normalized, 1 is raw
p_sws = [True for c in range(N_PATTERNS)]
p_modes = [1  for c in range(N_PATTERNS)] # mode 0 is normalized, 1 is raw
p_thresh = [True for c in range(N_PATTERNS)]
past_pth = [True for c in range(N_PATTERNS)]

actual_set = [0,0,0,0,0,0,""]
actual_patterns = [0,0,0,0]
pos = (0,0)
running = True
ii=0

canales = {}
timetags = []
ch_names = []
protos = []

# create plots for electrodes channels and pattern matchings
filename_csv = ""
PLOTS = [Plot(50+i*75, 300, 512, 70, CHANNELS[i], COLORS_ELEC[i]) for i in range(N_CHANNELS)]
PATTERN_MATCHES = [Plot(550+i*75, 300, 512, 70, PATTERNS[i],COLORS_PATS[i]) for i in range(N_PATTERNS)]


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
def init_osc(osc_host = OSC_HOST, osc_port = OSC_PORT):
    """
        Initialize OSC communications with HOST
    """
    global OSC_CLIENT
    OSC_CLIENT = OSCClient(osc_host, osc_port)
    return

def update_data(i=0):
    """
        Set new values in actual_set, reading it from canales 
    """
    global canales, ch_names, actual_set
    print("\n\n[sample]: ", i)
    #reload new data
    actual_set = [canales[k][i] for k in ch_names]
    return

def get_dtw():
    """
        Estimates the distance between current data showed in channel plot 
        and each of the training patterns. The distance should be interpreted as
        inverse to similarity, so a lower distance means more similarity or matching.
    """
    global protos, actual_patterns
    vector_a = np.array(([PLOTS[0].samples]), dtype=float)
    #print("--- V_B");print(vector_a);print(vector_a.shape)
    actual_patterns = []
    for a in range(N_PATTERNS):
        vector_b = np.array(([protos[a]]), dtype=float)
        #print("--- V_B");print(vector_b);print(vector_b.shape)
        dist, cost, acc, path = dtw([vector_a], [vector_b], dist_fun)
        #dist = pearsonr(v_a, v_b)[0]
        #dist = np.corrcoef(vector_a, vector_b)[0,1]
        #print (dist)
        actual_patterns.append(dist)
    return

def send_osc():
    """
        Manages the OSC message sending, by reading the states of switches, modes and threshold buttons-
        Calculates normalized and thresholded values on demand.
        Changes on OSC route requires updating the correpondant expression. that looks like this:
            ruta = '/potencial/{}'.format(ch.lower()) 

    """
    global ch_names, actual_set, OSC_CLIENT, past_pth
    # update ELECTRODES
    for j,ch in enumerate(ch_names):
        aux_val = float(actual_set[j])
        PLOTS[j].update(aux_val, ch)
        if (sws[j]):
            ruta = '/potencial/{}'.format(ch.lower())       #  <-   -   -OSC route for normalized/raw electrodes: normalized [0.0 -> 1.0], raw[-1000, 1000]
            ruta = ruta.encode()
            #print("{} \t{:0.3f}\t".format(ch, aux_val))
            if (modes[j]):
                OSC_CLIENT.send_message(ruta, [aux_val])
            else:
                nu_val = pmap(aux_val, -1000, 1000, 0 , 1)
                OSC_CLIENT.send_message(ruta, [nu_val])
            #    print("{} \t{:0.3f}\t({:d})".format(s, aux_mean, len(lista_mediciones)))
    # update PATTERNS
    for k, pm in enumerate(PATTERNS):
        aux_pat = float(actual_patterns[k])
        PATTERN_MATCHES[k].update(aux_pat, pm)
        if (p_sws[k]):
            ruta = '/potencial/pattern/{}'.format(pm.lower())#  <-   -   -OSC route for normalized/raw pattern: normalized [0.0 -> 1.0], raw [10000, 0]
            ruta = ruta.encode()
            #print("{} \t{:0.3f}\t".format(ch, aux_val))
            if (p_modes[k]):
                OSC_CLIENT.send_message(ruta, [aux_pat])
            else:
                nu_val = pmap(aux_pat, 0, 10000, 1 , 0)
                OSC_CLIENT.send_message(ruta, [nu_val])
                if (p_thresh[k]):
                    ruta = '/potencial/pattern/{}/thresh'.format(pm.lower()) #  <-   -OSC route for thresholded pattern: 1 when match 0 otherwise
                    ruta = ruta.encode()
                    if(nu_val>0.5):
                        pth = 1
                        OSC_CLIENT.send_message(ruta, [pth])
                    else:
                        pth = 0
                        OSC_CLIENT.send_message(ruta, [pth])
                    if (past_pth[k]!=pth):
                        past_pth[k] = pth
                        ruta = '/potencial/pattern/{}/on/'.format(pm.lower())#  <-   -OSC route for recognized pattern: 1 when start matching, 0 when ends
                        ruta = ruta.encode()
                        OSC_CLIENT.send_message(ruta, [pth])
    return



def load_data_csv(filename_csv):
    """
        Loads columns of csv files as timeseries 
            t	AF3	    F7	    F3	    F4	    F8	    AF7
    
    """
    global canales, timetags, ch_names
    data = read_csv(filename_csv)
    canales["AF3"] = data["AF3"].tolist()
    canales["F7"] = data["F7"].tolist()
    canales["F3"] = data["F3"].tolist()
    canales["F4"] = data["F4"].tolist()
    canales["F8"] = data["F8"].tolist()
    canales["AF7"] = data["AF7"].tolist()
    #timetags = data["_t"].tolist()
    ch_names = sorted(list(canales.keys()))
    print ("[DATA_CSV]: ok")
    return

def load_protos(filename_protos):
    """
        
p_modes = [1  for c in range(N_PATTERNS)] Loads training instances, 
        Add instances to allow more recognized patterns 
    """
    global protos
    data2 = read_csv(filename_protos)
    protos.append(data2["PAT1"].tolist())
    protos.append(data2["PAT2"].tolist())
    protos.append(data2["PAT3"].tolist())
    protos.append(data2["PAT4"].tolist())
    return

# functions
def isFloat(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False

# tic for the timer
def tic():
    global ii
    # send osc messages
    update_data(ii)
    get_dtw()
    send_osc()
    # update 
    if (ii<len(canales[ch_names[0]])-1):
        ii = ii+1
    else:
        ii=0
    #ii = ii+1
    #print ("\t\t -->   Aqui ENVIA DATOS")
    return

def exit_():
    global running
    running=False
    return

# keys handler
def handle_keys(event):
    global running
    if (event.key == pygame.K_ESCAPE):
        running = False

# event handler with a dictionay
def handle_events():
    event_dict = {
        pygame.QUIT: exit_,
        pygame.KEYDOWN: handle_keys,
        TIC_EVENT: tic
        }
    for event in pygame.event.get():
        if event.type in event_dict:
            if (event.type==pygame.KEYDOWN):
                event_dict[event.type](event)
            else:
                event_dict[event.type]()
    return

# click handler
def handle_mouse_clicks():
    global sws, modes
    # check for mouse pos and click
    pos = pygame.mouse.get_pos()
    b1, b2, b3 = pygame.mouse.get_pressed()
    # Check collision between buttons (switches) and mouse1
    for j,b in enumerate(CH_SWITCHES):
        if (b.collidepoint(pos) and b1):
            sws[j] = not (sws[j])
            #if (sws[j]==True):
            #    conts[j] = conts[j]+1
            print("[SW{}]!: ".format(j), sws[j])
    # Check collision between buttons (modes) and mouse1
    for j,b in enumerate(CH_MODES):
        if (b.collidepoint(pos) and b1):
            modes[j] = int(not modes[j])
            print("[MD{}]!: ".format(j), modes[j])
    # Check collision between buttons (switches) and mouse1
    for j,b in enumerate(PM_SWITCHES):
        if (b.collidepoint(pos) and b1):
            p_sws[j] = not (p_sws[j])
            #if (sws[j]==True):
            #    conts[j] = conts[j]+1
            print("[P_SW{}]!: ".format(j), sws[j])
    # Check collision between buttons (modes) and mouse1
    for j,b in enumerate(PM_MODES):
        if (b.collidepoint(pos) and b1):
            p_modes[j] = int(not p_modes[j])
            print("[P_MD{}]!: ".format(j), p_modes[j])
    # Check collision between buttons (modes) and mouse1
    for j,b in enumerate(PM_THRESH):
        if (b.collidepoint(pos) and b1):
            p_thresh[j] = int(not p_thresh[j])
            print("[P_TH{}]!: ".format(j), p_thresh[j])
    return


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
def update_graphics():
    #updaye plots and other gui
    PLOTS_SCREEN.fill(COLOR_BG)
    for c in range(N_CHANNELS):
        # do plots
        o_x = 100+c*75
        o_y = 50+c*75
        PLOTS[c].draw_h(PLOTS_SCREEN, 50, o_y)
        # update CH_SWITCHES
        if(sws[c]): pygame.draw.rect(PLOTS_SCREEN, COLORS_ELEC[c], pygame.Rect(250+320, o_y, 30, 70), 0)
        else: pygame.draw.rect(PLOTS_SCREEN, COLORS_ELEC[c], pygame.Rect(250+320, o_y, 30, 70), 1)
        # upadte CH_MODES
        if(modes[c]): pygame.draw.rect(PLOTS_SCREEN, COLORS_ELEC[c], pygame.Rect(285+320, o_y, 30, 70), 0)
        else: pygame.draw.rect(PLOTS_SCREEN, COLORS_ELEC[c], pygame.Rect(285+320, o_y, 30, 70), 1)
    # update pattern matching plots
    for c in range(N_PATTERNS):
        # do plots
        o_x = 100+c*75
        o_y = 550+c*75
        PATTERN_MATCHES[c].draw_h(PLOTS_SCREEN, 50, o_y)
        # redo PM_SWITCHES
        if(p_sws[c]): pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(250+320, o_y+35, 65, 30), 0)
        else: pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(250+320, o_y+35, 65, 30), 1)
        # redo PM_MODES
        if(p_modes[c]): pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(250+320, o_y, 30, 30), 0)
        else: pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(250+320, o_y, 30, 30), 1)
        # redo PM_THRESH
        if(p_thresh[c]): pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(285+320, o_y, 30, 30), 0)
        else: pygame.draw.rect(PLOTS_SCREEN, COLORS_PATS[c], pygame.Rect(285+320, o_y, 30, 30), 2)
    # blit on WINDOW
    WINDOW.blit(PLOTS_SCREEN, (0, 0))
    pygame.display.flip()
    return

def update_text():
    # update labels and other texts
    global LABELS, actual_set, actual_set_means
    AUX_LABEL = FONT.render('-> i n t e r s p e c i f i c s : ', 1, (32, 48, 0))
    WINDOW.blit(AUX_LABEL, (50, 25))
    AUX_LABEL = FONT.render(' [ POTENCIAL DE ACCIÓN ]', 1, (64, 32, 128))
    WINDOW.blit(AUX_LABEL, (360, 25))
    COUNT_LABEL = FONT.render("[step]:  {}".format(ii), 1, (16,64,32))
    # blit on WINDOW
    WINDOW.blit(COUNT_LABEL, (50, 870))
    pygame.display.flip()
    return


# ... .... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ...
def game_loop():
    # the app loop
    while running:
        handle_events()
        handle_mouse_clicks()
        update_graphics()
        update_text()
        clock.tick(30)

# the main (init+loop)
def main():
    pygame.display.set_caption(' . POTENCIAL DE ACCIÓN .')
    init_osc()
    load_protos("./data/protos_256.csv")                                    #  <-   -   -   -name of TRAINING file
    load_data_csv("./data/EEGdata_02_ReducFilterIC/valery_RF_ELEC.csv")     #  <-   -   -   -name of DATA file, can be any _ELEC.csv file in folder
    pygame.time.set_timer(TIC_EVENT, TIC_TIMER)
    game_loop()
    print("END OF TRANSMISSION //...")
    

if __name__=="__main__":
    main()



# -------------------------------------------------------------------------------

