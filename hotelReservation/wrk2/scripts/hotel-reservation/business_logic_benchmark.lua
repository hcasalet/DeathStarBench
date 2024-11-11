local socket = require("socket")
math.randomseed(socket.gettime()*1000)
math.random(); math.random(); math.random()

local url = "http://localhost:5000"

local function benchmark_fast()
    local large_response = math.random(0, 1)
    local num_kb = math.random(1, 10)
  
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
  local slow_ratio      = 0.01
  local fast_ratio   = 0.99

  large_message_kb = 10
  small_message_kb = 1

  local coin = math.random()
  if coin < slow_ratio then
    return benchmark_slow(url)
  elseif coin < fast_ratio then
    return benchmark_fast(url)
  end
end
