% Define the parameters for data generation
brands = ["Amazon", "Walmart", "Coca-Cola", "Nestle", "Starbucks", "Other"];
% Weights are somewhat like https://www.sierraclub.org/sierra/just-five-companies-produce-nearly-25-percent-all-plastic-waste-worldwide
brand_weights = [0.1, 0.2, 0.4, 0.25, 0.1, 0.05];

cities = { {'San Francisco', 'CA'}, {'New York', 'NY'}, {'Los Angeles', 'CA'}, {'Austin', 'TX'}, {'Chicago', 'IL'}, {'Princeton', 'NJ'} };

descriptions = ["cardboard box", "plastic cup", "aluminum can", "paper bag", "plastic bottle"];
waste_types = ["compostable", "recyclable", "trash"];

% Define the time range for waste items (e.g., the past week)
start_time = datetime('now') - days(7);
end_time = datetime('now');
time_range = start_time:hours(1):end_time;

% Define probabilities to make certain brands appear more wasteful
brand_recycling_weights = containers.Map({'Amazon', 'Walmart', 'Coca-Cola', 'Nestle', 'Starbucks', 'Other'}, [0.9, 0.25, 0.95, 0.95, 0.7, 0.3]);

brand_compost_weights = containers.Map({'Amazon', 'Walmart', 'Coca-Cola', 'Nestle', 'Starbucks', 'Other'}, [0.1, 0.5, 0, 0.02, 0.3, 0.2]);

hour_compost_weights = [0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.2, 0.3, 0.4, 0.6, 0.5, 0.6,...
                        0.7, 0.6, 0.3, 0.2, 0.2, 0.4, 0.6, 0.6, 0.5, 0.4, 0.3, 0.1];

max_hour_compost_weight = max(hour_compost_weights);  % which is 0.7

% Number of data entries to generate
N = 2500;

% Initialize output array
data(N) = struct("filename", "", "time", "", "state", "", "city", "", "description", "", "is_recyclable", 0, "is_compostable", 0, "is_metal", 0, "brand", "");

adjectives = ["tiny", "small", "medium", "large", "ultra large", "gigantic"];

for i = 1:N
    % Generate random time within time_range
    time_idx = randi(length(time_range));
    time = time_range(time_idx);
    hour = time.Hour;
    
    % Randomly select a city and state
    city_state = cities{randi(length(cities))};
    city = city_state{1};
    state = city_state{2};
    
    % Randomly select a brand using the adjusted weights
    brand = randsample(brands, 1, true, brand_weights);
    
    % Randomly select a description
    description = descriptions(randi(length(descriptions)));
    
    % Adjust description with random adjectives
    adjective = adjectives(randi(length(adjectives)));
    description = adjective + " " + description;
    
    % Determine is_metal based on description
    is_metal = contains(description, "aluminum can");
    
    % Determine is_recyclable
    if isKey(brand_recycling_weights, brand)
        recycling_prob = brand_recycling_weights(brand);
    else
        recycling_prob = 0.5;
    end
    is_recyclable = rand() < recycling_prob;
    
    % Determine is_compostable
    if isKey(brand_compost_weights, brand)
        compost_prob_brand = brand_compost_weights(brand);
    else
        compost_prob_brand = 0.1;
    end
    compost_prob_hour = hour_compost_weights(hour+1) / max_hour_compost_weight;
    compost_prob = compost_prob_brand * compost_prob_hour * 3;  % increase rate
    is_compostable = rand() < compost_prob;
    
    % Create item struct
    item.filename = sprintf('%d.jpg', i-1);
    item.time = datestr(time, 'yyyy-mm-ddTHH:MM:SS');
    item.state = state;
    item.city = city;
    item.description = description;
    item.is_recyclable = is_recyclable;
    item.is_compostable = is_compostable;
    item.is_metal = is_metal;
    item.brand = brand;
    
    % Store item in data
    data(i) = item;
end

% Output data to JSON
fid = fopen('result.json', 'w');
fprintf(fid, jsonencode(data));
fclose(fid);
