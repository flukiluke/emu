#!/usr/bin/env python3
# License: https://creativecommons.org/publicdomain/zero/1.0/legalcode
# Frequency analysis code based on https://github.com/aubio/aubio/blob/master/python/demos/demo_alsa.py under GPL3
import alsaaudio, numpy as np, aubio
NOTEOF = {72: 0, 74: 1, 76: 2, 79: 3, 81: 4};MAPPING = {0:{1:0,2:1,3:2,4:3},1:{0:4,2:5,3:6,4:7},2:{0:8,1:9,3:10,4:11},3:{0:12,1:13,2:14,4:15},4:{0:16,1:17,2:{0:18,1:19,3:20,4:21},3:{0:22,1:23,2:24,4:25}}}
class Machine(object):
    def __init__(self, stack = [], variables = {}, functions = {}):
        self.stack = stack;self.control = [];self.cts = [];self.ip = 0;self.variables = variables;self.functions = functions
    def feed(self, program):self.ip = 0;self.program = program
    def run(self):
        while self.ip < len(self.program):
            s = self
            if s.program[s.ip] == 11: return
            exec(['s.push(s.pop2())','s.push(int(s.program[s.ip+1]));s.ip+=1','s.push(s.stack[-2])','print(s.pop())','s.push(s.stack[-1])','','if self.pop():\n s.control.append((-1,0,0))\nelse:\n n=1\n while s.program[s.ip]!=7 or n:\n  s.ip+=1\n  if s.program[s.ip]==6:n+=1\n  if s.program[s.ip]==7:n-=1','','step=s.pop();start=s.pop();end=s.pop()\nif start > end:\n n=1\n while s.program[s.ip]!=9 or n:\n  s.ip+=1\n  if s.program[s.ip]==8:n+=1\n  if s.program[s.ip]==9:n-=1\nelse:s.control.append((s.ip,step,end));s.cts.append(start)','s.cts[-1]+=s.control[-1][1]\nif s.cts[-1]<=s.control[-1][2]:s.ip=s.control[-1][0]\nelse:s.cts.pop();s.control.pop()','s.push(s.cts[-1])','','s.push(s.pop()*s.pop())','s.push(s.pop2()//s.pop())','name = s.program[s.ip+1];s.ip+=2;function=[]\nwhile s.program[s.ip]!=5:\n function.append(s.program[s.ip]);s.ip+=1\ns.functions[name]=function','call=Machine(stack=s.stack,variables=s.variables,functions=s.functions);call.feed(s.functions[s.program[s.ip+1]]);call.run();s.ip+=1','s.push(s.pop()+s.pop())','s.push(s.pop2()-s.pop())','s.variables[s.program[s.ip+1]]=s.pop();s.ip+=1','s.push(s.variables[s.program[s.ip+1]]);s.ip+=1','','s.push(int(s.pop2()<s.pop()))','s.push(int(s.pop2()>s.pop()))','s.push(int(self.pop()==self.pop()))','s.push(s.pop2()%s.pop())','s.push(s.cts[-2])'][s.program[s.ip]])
            s.ip += 1
    def push(self, v):self.stack.append(v)
    def pop(self):return self.stack.pop()
    def pop2(self):r = self.stack[-2];del self.stack[-2];return r

class Sequencer(object):
    def __init__(self, threshhold, note_min, note_max):
        self.note_min = note_min;self.note_max = note_max;self.buf = [];self.prev_seq = None;self.seqs = [];self.threshhold = threshhold;self.num_mode = False;self.numstep1 = True;self.num = ''
    def new_note(self, new_note):
        if new_note < self.note_min or new_note > self.note_max:
            return
        if len(self.buf) == 0:
            self.buf = [new_note]
        elif self.buf[0] == new_note:
            self.buf.append(new_note)
        else:
            self.buf = [new_note]
        if len(self.buf) == self.threshhold:
            self.buf.clear()
            if self.prev_seq != new_note:
                ps = self.prev_seq
                self.prev_seq = new_note
                if self.num_mode and new_note == 84:
                    self.numstep1 = True
                    self.seqs.append(self.num)
                    self.num = ''
                elif self.num_mode and not self.numstep1:
                    self.num += str(int(abs(ps - new_note)) % 10)
                    self.numstep1 = True
                elif self.num_mode:
                    self.numstep1 = False
                else:
                    self.seqs.append(new_note)
    def next_seq(self):
        if self.num_mode and len(self.seqs) and type(self.seqs[-1]) == str:
            self.num_mode = False
            return self.seqs.pop(0)
        m = MAPPING
        i = 0
        while i < len(self.seqs) and type(m) != int:
            if self.seqs[i] in NOTEOF:
                n = NOTEOF[self.seqs[i]]
                try:
                    m = m[n]
                except KeyError:
                    del self.seqs[i]
            i += 1
        if type(m) == int:
            self.seqs = self.seqs[i:]
            return m
        return False

samplerate = 44100;win_s = 2048;hop_s = win_s // 2;framesize = hop_s
recorder = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
recorder.setperiodsize(framesize)
recorder.setrate(samplerate)
recorder.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
recorder.setchannels(1)
pitcher = aubio.pitch("default", win_s, hop_s, samplerate)
pitcher.set_unit("midi")
pitcher.set_silence(-40)
sequencer = Sequencer(5, 72, 84)
machine = Machine()
program = []
num_mode = False

while True:
    _, data = recorder.read()
    samples = np.fromstring(data, dtype=aubio.float_type)
    note = pitcher(samples)[0]
    sequencer.new_note(round(note))
    seq = sequencer.next_seq()
    if seq == 20:
        machine.feed(program)
        machine.run()
    elif seq in [1, 14, 15, 18, 19]:
        program.append(seq)
        sequencer.num_mode = True
    elif seq is not False:
        program.append(int(seq))
