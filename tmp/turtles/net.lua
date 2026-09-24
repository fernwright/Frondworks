-- net.lua
-- Modem discovery + rednet helpers for the BalschiCraft turtle fleet.
-- Works whether the wireless modem is an equipped turtle upgrade or an
-- adjacent block: we find it by peripheral type, not by side name.

local net = {}

net.PROTOCOL = "balschi"

local opened = false

-- Find a modem peripheral and open rednet on it. Returns true on success.
function net.open()
  if opened then return true end
  for _, name in ipairs(peripheral.getNames()) do
    if peripheral.getType(name) == "modem" then
      rednet.open(name)
      opened = true
      return true
    end
  end
  return false
end

function net.send(target, msg) rednet.send(target, msg, net.PROTOCOL) end
function net.broadcast(msg) rednet.broadcast(msg, net.PROTOCOL) end
function net.receive(timeout) return rednet.receive(net.PROTOCOL, timeout) end

return net
