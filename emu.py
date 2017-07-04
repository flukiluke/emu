#!/usr/bin/python3
import sys

class Machine(object):
    def __init__(self, stack = [], variables = {}, functions = {}):
        self.stack = stack
        self.control = []
        self.cts = []
        self.ip = 0
        self.variables = variables
        self.functions = functions
        self.commands = ['DMP', 'RET', 'OUT', 'DIG', 'NUM', 'STR', 'DUP', 'SWP', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'LST', 'GRT', 'EQU', 'BCO', 'ECO', 'BIT', 'EIT', 'CT1', 'CT2', 'STO', 'RCL', 'DEF', 'FUN', 'INP', 'IND', 'LEN']

    def feed(self, program):
        self.ip = 0
        self.program = program

    def run(self):
        while self.ip < len(self.program):
            opcode = self.program[self.ip]
            if opcode not in self.commands:
                self.funccall(opcode)
            else:
                if getattr(self, 'cmd_' + opcode)():
                    return True
            self.ip += 1
            #print(self.stack)

    def funccall(self, func):
        if func not in self.functions:
            raise SyntaxError('Unknown command: ' + func)
        call = Machine(stack = self.stack, variables = self.variables, functions = self.functions)
        call.feed(self.functions[func])
        call.run()

    def push(self, v):
        self.stack.append(v)

    def pop(self):
        if len(self.stack) == 0:
            raise BufferError
        return self.stack.pop()

    def pop2(self):
        if len(self.stack) < 2:
            raise BufferError
        r = self.stack[-2]
        del self.stack[-2]
        return r

    def cmd_DMP(self):
        print(self.stack)

    def cmd_SWP(self):
        self.push(self.pop2())

    def cmd_NUM(self):
        n = self.program[self.ip + 1]
        if '.' in n:
            self.push(float(n))
        else:
            self.push(int(n))
        self.ip += 1

    def cmd_STR(self):
        self.push(self.program[self.ip + 1].replace(';N', '\n').replace(';S', ' ').replace(';;', ';'))
        self.ip += 1

    def cmd_DIG(self):
        if len(self.stack) < 2:
            raise BufferError
        self.push(self.stack[-2])

    def cmd_OUT(self):
        print(self.pop())

    def cmd_INP(self):
        self.push(input())

    def cmd_IND(self):
        if len(self.stack) < 2:
            raise BufferError
        self.push(self.stack[-2][self.pop() - 1])

    def cmd_LEN(self):
        if len(self.stack) < 1:
            raise BufferError
        self.push(len(self.stack[-1]))

    def cmd_DUP(self):
        if len(self.stack) < 1:
            raise BufferError
        self.push(self.stack[-1])

    def cmd_BCO(self):
        if self.pop():
            self.control.append((-1,0,0))
        else:
            n=1
            while self.program[self.ip] != 'ECO' or n:
                self.ip += 1
                if self.program[self.ip] == 'BCO':
                    n += 1
                elif self.program[self.ip] == 'ECO':
                    n -= 1

    def cmd_ECO(self):
        if len(self.control) == 0 or self.control.pop()[0] != -1:
            raise SyntaxError('ECO without matching BCO')

    def cmd_BIT(self):
        step = self.pop()
        start = self.pop()
        end = self.pop()
        if start > end:
            n = 1
            while self.program[self.ip] != 'EIT' or n:
                self.ip += 1
                if self.program[self.ip] == 'BIT':
                    n += 1
                elif self.program[self.ip] == 'EIT':
                    n -= 1
        else:
            self.control.append((self.ip, step, end))
            self.cts.append(start)

    def cmd_EIT(self):
        if len(self.control) == 0 or self.control[-1][0] == -1:
            raise SyntaxError('EIT without matching BIT')
        self.cts[-1] += self.control[-1][1]
        if self.cts[-1] <= self.control[-1][2]:
            self.ip = self.control[-1][0]
        else:
            self.cts.pop()
            self.control.pop()

    def cmd_CT1(self):
        if len(self.cts) < 1:
            raise SyntaxError('CT1 outside BIT')
        self.push(self.cts[-1])

    def cmd_CT2(self):
        if len(self.cts) < 2:
            raise SyntaxError('CT2 outside nested BIT')
        self.push(self.cts[-2])

    def cmd_RET(self):
        return True

    def cmd_ADD(self):
        self.push(self.pop2() + self.pop())
 
    def cmd_SUB(self):
        self.push(self.pop2() - self.pop())

    def cmd_MUL(self):
        self.push(self.pop2() * self.pop())

    def cmd_DIV(self):
        self.push(self.pop2() / self.pop())

    def cmd_MOD(self):
        self.push(self.pop2() % self.pop())

    def cmd_LST(self):
        self.push(int(self.pop2() < self.pop()))

    def cmd_GRT(self):
        self.push(int(self.pop2() > self.pop()))

    def cmd_EQU(self):
        self.push(int(self.pop() == self.pop()))

    def cmd_STO(self):
        self.variables[self.program[self.ip + 1]] = self.pop()
        self.ip += 1

    def cmd_RCL(self):
        if self.program[self.ip + 1] not in self.variables:
            raise UnboundLocalError
        self.push(self.variables[self.program[self.ip + 1]])
        self.ip += 1

    def cmd_DEF(self):
        name = self.program[self.ip + 1]
        self.ip += 2
        function = []
        while self.program[self.ip] != 'DEF':
            function.append(self.program[self.ip])
            self.ip += 1
        self.functions[name] = function


def do(machine, program):
        machine.feed(program.upper().split())
        try:
            if machine.run():
                exit()
        except SyntaxError as e:
            print(e)
        except BufferError:
            print('Stack underflow')
        except IndexError:
            print('Execution past end of program')
        except UnboundLocalError:
            print('Invalid variable access')
        except ValueError:
            print('Invalid number')
        except TypeError:
            print('Type mismatch')
        else:
            return True

if __name__ == '__main__':
    machine = Machine()

    if len(sys.argv) >= 2:
        for sourcefile in sys.argv[1:]:
            if not sourcefile.endswith('.emu'):
                sourcefile += '.emu'
            f = open(sourcefile, 'r')
            program = ' '.join([x.strip(' \n') for x in f.readlines() if len(x.strip()) and x.strip()[0] != '#'])
            if do(machine, program) is not True:
                exit()
            
        
    while True:
        try:
            strin = input("> ")
        except EOFError:
            print()
            exit()
        do(machine, strin)


