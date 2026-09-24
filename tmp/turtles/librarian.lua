-- librarian.lua
-- Storage-aisle librarian turtle. Serves chests at (ax, ay, s) over rednet.
--
-- Install: place at world (10,-1,12) facing +x (east), with a wireless modem
-- equipped (craft turtle + modem). Then:
--   wget https://frondworks.com/tmp/turtles/nav.lua nav.lua
--   wget https://frondworks.com/tmp/turtles/net.lua net.lua
--   wget https://frondworks.com/tmp/turtles/librarian.lua librarian.lua
-- Add `shell.run("librarian.lua")` to startup.lua so it resumes after reboots.
--
-- Protocol "balschi". Commands (tables) and replies:
--   {cmd="ping"}                      -> {ok, id, pong}
--   {cmd="status"}                    -> {ok, id, pos, heading, fuel, fuelMax}
--   {cmd="goto", ax, ay, s}           -> face a chest
--   {cmd="suck", ax, ay, s, count?, slot?} -> suck items, report diff
--   {cmd="drop", ax, ay, s, slot?, count?} -> drop items into chest
--   {cmd="audit", ax, ay, s}          -> full chest manifest (sucks all, puts back)
--   {cmd="refuel"}                    -> refuel from FUEL_CHEST

local nav = dofile("nav.lua")
local net = dofile("net.lua")

local ID = "librarian-1"
local FUEL_MIN = 400 -- auto-refuel below this level
local FUEL_CHEST = { ax = 8, ay = 0, s = 1 } -- stock ONLY with coal/charcoal

if not net.open() then
  print("No wireless modem found. Equip one and reboot.")
  return
end
rednet.host(net.PROTOCOL, ID)

-- Burn any fuel already sitting in the inventory (first-boot convenience).
local function burnAll()
  for i = 1, 16 do
    turtle.select(i)
    while turtle.getFuelLevel() < turtle.getFuelLimit() and turtle.refuel() do end
  end
  turtle.select(1)
end
burnAll()

nav.gpsFix(5)
net.broadcast({ kind = "hello", id = ID, pos = nav.getPos(), fuel = turtle.getFuelLevel() })
print("Librarian " .. ID .. " online. Fuel: " .. turtle.getFuelLevel())

-- ---------- inventory helpers ----------

local function scan()
  local items = {}
  for i = 1, 16 do
    local d = turtle.getItemDetail(i)
    if d then
      items[#items + 1] = { slot = i, name = d.name, count = d.count, display = d.displayName }
    end
  end
  return items
end

local function dropAll()
  for i = 1, 16 do
    if turtle.getItemCount(i) > 0 then
      turtle.select(i)
      turtle.drop()
    end
  end
  turtle.select(1)
end

-- Suck one stack-ish pull, using the first slot with room.
local function suckStack(count)
  for i = 1, 16 do
    if turtle.getItemSpace(i) > 0 then turtle.select(i) break end
  end
  local ok = turtle.suck(count)
  turtle.select(1)
  return ok
end

local function refuel()
  local ok, err = nav.faceChest(FUEL_CHEST.ax, FUEL_CHEST.ay, FUEL_CHEST.s)
  if not ok then return false, err end
  while suckStack() do end
  burnAll()
  dropAll()
  nav.toLane()
  return true
end

local function ensureFuel()
  if turtle.getFuelLevel() >= FUEL_MIN then return true end
  print("Low fuel (" .. turtle.getFuelLevel() .. "), refueling...")
  local ok, err = refuel()
  if not ok then return false, err end
  if turtle.getFuelLevel() < FUEL_MIN then
    return false, "still low after refuel (" .. turtle.getFuelLevel() .. ")"
  end
  return true
end

-- ---------- command handlers ----------

local handlers = {}

handlers.ping = function()
  return { ok = true, pong = true }
end

handlers.status = function()
  return {
    ok = true, pos = nav.getPos(), heading = nav.getHeading(),
    fuel = turtle.getFuelLevel(), fuelMax = turtle.getFuelLimit(),
  }
end

handlers.goto = function(m)
  local ok, err = nav.faceChest(m.ax or 0, m.ay or 0, m.s or 0)
  if not ok then return { ok = false, err = err, pos = nav.getPos() } end
  return { ok = true, pos = nav.getPos() }
end

handlers.suck = function(m)
  local ok, err = nav.faceChest(m.ax or 0, m.ay or 0, m.s or 0)
  if not ok then return { ok = false, err = err } end
  local before = scan()
  if m.slot and m.slot >= 1 and m.slot <= 16 then
    turtle.select(m.slot)
    turtle.suck(m.count or 64)
    turtle.select(1)
  else
    suckStack(m.count or 64)
  end
  return { ok = true, before = before, after = scan(), pos = nav.getPos() }
end

handlers.drop = function(m)
  local ok, err = nav.faceChest(m.ax or 0, m.ay or 0, m.s or 0)
  if not ok then return { ok = false, err = err } end
  if m.slot and m.slot >= 1 and m.slot <= 16 then
    turtle.select(m.slot)
    turtle.drop(m.count or 64)
    turtle.select(1)
  else
    dropAll()
  end
  nav.toLane()
  return { ok = true, inventory = scan() }
end

handlers.audit = function(m)
  local ok, err = nav.faceChest(m.ax or 0, m.ay or 0, m.s or 0)
  if not ok then return { ok = false, err = err } end
  local manifest = {}
  while true do
    while suckStack() do end -- suck until turtle full or chest empty
    local items = scan()
    if #items == 0 then break end
    for _, it in ipairs(items) do
      local e = manifest[it.name]
      if not e then
        e = { name = it.name, display = it.display, count = 0 }
        manifest[it.name] = e
      end
      e.count = e.count + it.count
    end
    dropAll() -- put everything back before the next pass
  end
  local list = {}
  for _, e in pairs(manifest) do list[#list + 1] = e end
  nav.toLane()
  return { ok = true, chest = { ax = m.ax, ay = m.ay, s = m.s }, items = list }
end

handlers.refuel = function()
  local ok, err = refuel()
  if not ok then return { ok = false, err = err } end
  return { ok = true, fuel = turtle.getFuelLevel() }
end

-- ---------- main loop ----------

while true do
  local from, msg = net.receive()
  if type(msg) == "table" and type(msg.cmd) == "string" and handlers[msg.cmd] then
    local r
    if msg.cmd == "ping" or msg.cmd == "status" then
      local ok, res = pcall(handlers[msg.cmd], msg)
      r = ok and res or { ok = false, err = tostring(res) }
    else
      local fok, ferr = ensureFuel()
      if not fok then
        r = { ok = false, err = "fuel: " .. tostring(ferr) }
      else
        local ok, res = pcall(handlers[msg.cmd], msg)
        r = ok and res or { ok = false, err = tostring(res) }
      end
    end
    r.id = ID
    net.send(from, r)
  end
end
