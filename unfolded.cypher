CALL () {
    CALL () {
        CALL () {
            //------------------------ Follows(A,B) -------------------------
              // P1 – Following relation
              // Vehicle A follows vehicle B (same lane, B ahead)

              WITH
                100 AS stepSize

              MATCH (a_s1:object_state)-[:OF]->(a:object)
              WHERE a_s1.following IS NOT NULL
                AND a_s1.following <> 0
                AND a_s1.lane_id IS NOT NULL

              WITH a.id AS vehicle_id,
                  a_s1.following AS following_vehicle_id,
                  a_s1.lane_id AS lane,
                  a_s1.timestamp AS timestamp,
                  stepSize
              ORDER BY vehicle_id, following_vehicle_id, timestamp ASC

              WITH vehicle_id, following_vehicle_id, stepSize,
                  collect(timestamp) AS timestamps,
                  collect(lane) AS lanes

              // Build P1 intervals by scanning the ordered timestamps.
              WITH vehicle_id, following_vehicle_id, lanes, timestamps, stepSize,
                reduce(
                  acc = {
                    intervals: [],
                    start: timestamps[0],
                    prev: timestamps[0],
                    lane: lanes[0],
                    intervalTimestamps: [timestamps[0]],
                    countStates: 1
                  },  
                  i IN range(1, size(timestamps) - 1) |
                  CASE
                    WHEN timestamps[i] = acc.prev + stepSize
                      AND lanes[i] = acc.lane
                    THEN {
                      intervals: acc.intervals,
                      start: acc.start,
                      prev: timestamps[i],
                      lane: acc.lane,
                      intervalTimestamps: acc.intervalTimestamps + [timestamps[i]],
                      countStates: acc.countStates + 1
                    }
                    ELSE {
                      intervals: acc.intervals + [{
                        start: acc.start,
                        end: acc.prev,
                        lane: acc.lane,       
                        timestamps: acc.intervalTimestamps,     
                        lanes: acc.intervalLanes,
                        numberOfStates: acc.countStates
                      }],
                      start: timestamps[i],
                      prev: timestamps[i],
                      lane: lanes[i],
                      intervalTimestamps: [timestamps[i]],
                      countStates: 1
                    }
                  END
                ) AS result   

              // Append the final open P1 interval.
              WITH vehicle_id, following_vehicle_id, result.intervals + [{
                start: result.start,
                end: result.prev,
                lane: result.lane,
                timestamps: result.intervalTimestamps,      
                numberOfStates: result.countStates
              }] AS P1Intervals   

              UNWIND P1Intervals AS P1Interval
              RETURN vehicle_id, following_vehicle_id, 
                  P1Interval.start AS P1_start, 
                  P1Interval.end AS P1_end, 
                  P1Interval.lane AS P1_lane, 
                  //P1Interval.timestamps AS timestamps, 
                  P1Interval.numberOfStates AS P1_numberOfStates
        }
        RETURN DISTINCT
            'http://example.org/traffic#vehicle_' + toString(vehicle_id) AS tp0_x, 'http://example.org/traffic#vehicle_' + toString(following_vehicle_id) AS tp0_y, toString(P1_start) AS tp0_start, toString(P1_end) AS tp0_end
    }

    WITH tp0_x, tp0_y, tp0_start, tp0_end

    RETURN collect(
        DISTINCT {tp0_x: tp0_x, tp0_y: tp0_y, tp0_start: tp0_start, tp0_end: tp0_end}
    ) AS tp0_rows
}

UNWIND tp0_rows AS tp0_row

WITH *, tp0_row.tp0_x AS tp0_x, tp0_row.tp0_y AS tp0_y, tp0_row.tp0_start AS tp0_start, tp0_row.tp0_end AS tp0_end

RETURN 
    tp0_x AS x,
    tp0_y AS y,
    tp0_start AS start,
    tp0_end AS end