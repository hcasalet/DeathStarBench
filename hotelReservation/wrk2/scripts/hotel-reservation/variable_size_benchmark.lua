local socket = require("socket")
math.randomseed(socket.gettime()*1000)
math.random(); math.random(); math.random()

local url = "http://localhost:5000"

local function benchmark_fast()
    local large_response = "false"
  
    local method = "GET"
    local path = url .. "/benchmark/fast?large_response=" .. large_response .. "&num_kb=" .. num_kb
    local headers = {}
    return wrk.format(method, path, headers, nil)
end 

local function benchmark_slow()
  local large_response = math.random(0, 1)
  local num_kb = math.random(1, 10)

  local method = "GET"
  local path = url .. "/benchmark/slow?large_response=" .. large_response .. "&num_kb=" .. num_kb
  local headers = {}
  return wrk.format(method, path, headers, nil)
end

request = function()
  cur_time = math.floor(socket.gettime())
  local large_ratio      = 0.25
  local small_ratio   = 0.75

  large_message_kb = 1000
  small_message_kb = 1

  local coin = math.random()
  if coin < small_ratio then
    num_kb = small_message_kb
    return benchmark_fast(url, num_kb)
  elseif coin < small_ratio + large_ratio then
    num_kb = large_message_kb
    return benchmark_slow(url, num_kb)
  end
end
