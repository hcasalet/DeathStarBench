local socket = require("socket")
math.randomseed(socket.gettime()*1000)
math.random(); math.random(); math.random()

local url = "http://localhost:5000"

local function benchmark_fast()
    local large_response = false
  
    local method = "GET"
    local path = url .. "/benchmark/fast?large_response=" .. large_response .. "&num_kb=" .. num_kb
    local headers = {}
    return wrk.format(method, path, headers, nil)
end 

request = function()
  cur_time = math.floor(socket.gettime())
  local large_ratio      = 0.1
  local small_ratio   = 0.9

  large_message_kb = 10
  small_message_kb = 1

  local coin = math.random()
  if coin < large_ratio then
    num_kb = large_message_kb
    return benchmark_fast(url, num_kb)
  elseif coin < small_ratio then
    num_kb = small_message_kb
    return benchmark_fast(url, num_kb)
  end
end
