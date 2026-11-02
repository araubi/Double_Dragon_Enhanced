"""Drive a full play-through of the 7 missions with pseudo-random input.
Frame marker = E612h (shared blit hook). Per-mission title loop / completion check addresses."""
import random, time
from ramgame import RamGame

TITLE = {1: 0x919F, 2: 0x91E0, 3: 0x91E2, 4: 0x91D0, 5: 0x91EA, 6: 0x91E2}
CHECK = {1: (0x910C, 0x95BA), 2: (0x912B, 0x967B), 3: (0x9128, 0x9662), 4: (0x9116, 0x964F),
         5: (0x912D, 0x96A3), 6: (0x9129, 0x9660)}
FRAME = 0xE612
KEYSET = ['LEFT', 'RIGHT', 'UP', 'DOWN', 'SPACE', 'W', 'A', 'S', 'D', 'SHIFT']


def boot(g):
    m = g.m
    assert g.run_until([0x0D03]) == 0x0D03
    m.key('SPACE'); m.run(3_000_000); m.key('SPACE', False)   # la ROM espera a que se suelte
    assert g.run_until([TITLE[1]]) == TITLE[1]
    m.key('SPACE'); assert g.run_until([FRAME]) == FRAME; m.key('SPACE', False)


def play(g, frames, rnd, on_frame=None):
    m = g.m
    for it in range(frames):
        if it % 6 == 0:
            m.release_all()
            for k in rnd.sample(KEYSET, 3):
                m.key(k)
        pc = g.run_until([FRAME], max_cycles=60_000_000)
        assert pc == FRAME, 'no frame'
        m.poke(0x5B08, 5)   # keep credits so random play never hits the tape-rewind game over
        if on_frame:
            on_frame(g, it)
        g.m.run(1)  # step off the breakpoint


def complete_and_next(g, mission):
    """Force the 'mission complete' branch; the next mission now loads by itself."""
    m = g.m; m.release_all()
    chk, flag = CHECK[mission]
    assert g.run_until([chk]) == chk
    m.poke(flag, 1); n = len(g.loads)
    nxt = mission + 1
    while True:
        pc = g.run_until([0x9056])
        assert pc == 0x9056
        if len(g.loads) >= n + 2:
            break
        m.run(1)
    if nxt in TITLE:
        assert g.run_until([TITLE[nxt]]) == TITLE[nxt]
    else:
        g.m.run(30_000_000)   # mission 7 title: different code, just wait
    m.key('SPACE'); assert g.run_until([FRAME], 200_000_000) == FRAME; m.key('SPACE', False)


def run(img, seed, frames=900, log=print, on_frame=None, shots=None):
    g = RamGame(img, det_seed=seed); rnd = random.Random(seed); t = time.time()
    boot(g)
    for mission in range(1, 8):
        play(g, frames, rnd, on_frame)
        log('mission %d done, cyc=%d loads=%s t=%.0fs' % (mission, g.m.cyc, g.loads[-2:], time.time() - t))
        if shots:
            g.m.screenshot('%s_m%d.png' % (shots, mission), 1)
        if mission < 7:
            complete_and_next(g, mission)
    return g


if __name__ == '__main__':
    g = run(open('../dd/mem.bin', 'rb').read(), 11, shots='shots/cov')
    m = g.m
    open('cov_exec.bin', 'wb').write(m.exec_map())
    open('cov_read.bin', 'wb').write(m.read_map())
    open('cov_write.bin', 'wb').write(m.write_map())
