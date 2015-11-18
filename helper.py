import codecs
import os

def func1():
    a = set()

    for root, dirs, files in os.walk('./texts'):
        for i in files:
            print i
            f = codecs.open(os.path.join(root, i), 'r', 'utf-8')
            for line in f:
                if not line.startswith('#'):
                    line = line.split('\t')
                    lex = line[12].split(',')
                    gr = line[13].split(',')
                    a |= set(lex + gr)
            f.close()

    print ', '.join(sorted(a))

def func2():
    for root, dirs, files in os.walk('./texts'):
        for i in files:
            if i.endswith('.prs'):
                print i
                f = codecs.open(os.path.join(root, i), 'r', 'utf-8')
                a = f.readlines()
                f.close()
                f = codecs.open(os.path.join(root, i), 'w', 'utf-8')
                f.write(a[0].strip()+'\t#stat\r\n')
                incorr = False
                inerr = False
                # for line in f:
                for line in a[1:]:
                    if line.startswith('#'):
                        f.write(line)
                        # pass
                    else:
                        # print line
                        line = line.split('\t')
                        line[-1] = line[-1].strip()
                        punctl = line[15]
                        punctr = line[16]
                        if '} / {*' in punctl:
                            stat = 'corr'
                            incorr = True
                            inerr = False
                            if '}' in punctr:
                                stat += ' end'
                                incorr = False
                        elif '{' in punctl:
                            stat = 'err'
                            inerr = True
                            incorr = False
                        elif '} / {*' in punctr:
                            stat = 'err'
                            inerr = False
                            incorr = False
                        elif '}' in punctr:
                            stat = 'corr end'
                            incorr = False
                            inerr = False
                        else:
                            if incorr:
                                stat = 'corr'
                            elif inerr:
                                stat = 'err'
                            else:
                                stat = ''
                        line.append(stat)
                        f.write('\t'.join(line)+'\r\n')
                f.close()


func2()