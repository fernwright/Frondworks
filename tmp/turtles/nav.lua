-- nav.lua
-- Dead-reckoning + GPS-assisted navigation for the BalschiCraft storage aisle.
--
-- World frame:
--   Aisle slots: world x = X0 + ax,  ax = 0..AX_MAX   (10..18)
--   Driving level: y = FLOOR (-1), lane z = LANE (12)
--   Chest (ax, ay, s): world (X0+ax, ay, s==0 and LEFT_Z or RIGHT_Z)  (z=11 / z=13)
-- Turtle drives down the aisle facing +x. s=0 (left) is -z, s=1 (right) is +z.
-- Turtles fly: "rise to row y" is just turtle.up() in the clear aisle column.

local nav = {}

nav.X0 = 10
nav.AX_MAX = 8
nav.FLOOR = -1
nav.LANE = 12
nav.LEFT_Z = 11
nav.RIGHT_Z = 13

-- heading: 0=+x, 1=+z, 2=-x, 3=-z
local pos = { x = nav.X0, y = nav.FLOOR, z = nav.LANE }
local heading = 0

local function track(dx, dy, dz, ok)
  if ok then
    pos.x = pos.x + dx
    pos.y = pos.y + dy
    pos.z = pos.z + dz
  end
  return ok
end

local function forward1()
  if heading == 0 then return track(1, 0, 0, turtle.forward())
  elseif heading == 1 then return track(0, 0, 1, turtle.forward())
  elseif heading == 2 then return track(-1, 0, 0, turtle.forward())
  else return track(0, 0, -1, turtle.forward()) end
end

local function up1() return track(0, 1, 0, turtle.up()) end
local function down1() return track(0, -1, 0, turtle.down()) end

function nav.turnTo(h)
  h = ((h % 4) + 4) % 4
  while heading ~= h do
    local d = (h - heading) % 4
    if d == 1 or d == 2 then
      turtle.turnRight()
      heading = (heading + 1) % 4
    else
      turtle.turnLeft()
      heading = (heading + 3) % 4
    end
  end
end

-- Return to the driving lane at floor level. Never digs: a blocked path is an error.
function nav.toLane()
  while pos.y > nav.FLOOR do
    if not down1() then return false, "blocked descending at " .. pos.x .. "," .. pos.y .. "," .. pos.z end
  end
  while pos.y < nav.FLOOR do
    if not up1() then return false, "blocked ascending at " .. pos.x .. "," .. pos.y .. "," .. pos.z end
  end
  if pos.z < nav.LANE then
    nav.turnTo(1)
    while pos.z < nav.LANE do
      if not forward1() then return false, "blocked moving in lane" end
    end
  elseif pos.z > nav.LANE then
    nav.turnTo(3)
    while pos.z > nav.LANE do
      if not forward1() then return false, "blocked moving in lane" end
    end
  end
  return true
end

function nav.toSlot(ax)
  ax = math.max(0, math.min(nav.AX_MAX, math.floor(ax)))
  local ok, err = nav.toLane()
  if not ok then return false, err end
  local tx = nav.X0 + ax
  if pos.x < tx then
    nav.turnTo(0)
    while pos.x < tx do
      if not forward1() then return false, "blocked in aisle near x=" .. pos.x end
    end
  elseif pos.x > tx then
    nav.turnTo(2)
    while pos.x > tx do
      if not forward1() then return false, "blocked in aisle near x=" .. pos.x end
    end
  end
  return true
end

-- Move to face chest (ax, ay, s). Ends adjacent to the chest, facing it.
function nav.faceChest(ax, ay, s)
  ay = math.max(0, math.floor(ay))
  local ok, err = nav.toSlot(ax)
  if not ok then return false, err end
  for _ = 1, ay - nav.FLOOR do
    if not up1() then return false, "blocked rising to row " .. ay end
  end
  nav.turnTo(s == 0 and 3 or 1)
  return true
end

-- Snap dead-reckoning to GPS. Returns true on success.
function nav.gpsFix(timeout)
  if not gps then return false end
  local x, y, z = gps.locate(timeout or 5)
  if x then
    pos.x = math.floor(x + 0.5)
    pos.y = math.floor(y + 0.5)
    pos.z = math.floor(z + 0.5)
    return true
  end
  return false
end

function nav.getPos() return { x = pos.x, y = pos.y, z = pos.z } end
function nav.getHeading() return heading end

-- Manual calibration (e.g. after placing the turtle by hand).
function nav.setPose(x, y, z, h)
  pos.x, pos.y, pos.z = x, y, z
  if h then nav.turnTo(h) end
end

return nav
