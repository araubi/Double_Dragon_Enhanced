local f=0
emu.register_frame_done(function()
  f=f+1
  if f%20==0 and f<=1600 then manager.machine.video:snapshot() end
  if f>1600 then manager.machine:exit() end
end)
