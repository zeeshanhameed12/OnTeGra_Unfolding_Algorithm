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
            'http://example.org/traffic#vehicle_' + toString(vehicle_id) AS tp0_x, 'http://example.org/traffic#vehicle_' + toString(following_vehicle_id) AS tp0_y, P1_start AS tp0_p1Start, P1_end AS tp0_p1End
    }

    WITH tp0_x, tp0_y, tp0_p1Start, tp0_p1End

    RETURN collect(
        DISTINCT {tp0_x: tp0_x, tp0_y: tp0_y, tp0_p1Start: tp0_p1Start, tp0_p1End: tp0_p1End}
    ) AS tp0_rows
}

CALL () {
    CALL () {
        CALL () {
            //P2 – Small headway

            //---------------------------------------------------------------------------
            // Parameters for interval construction.
            //---------------------------------------------------------------------------
            WITH
              3.0 AS headway_threshold, // Threshold for small headway in seconds
              500 AS min_duration, // Minimum duration for a valid scenario in milliseconds
              100 AS stepSize // Minimum duration between two consecutive states
            // ---------------------------------------------------------------------------
            // P2: Small headway relation
            // ---------------------------------------------------------------------------
            MATCH (s:object_state)-[:OF]->(v:object)
            WHERE s.space_headway IS NOT NULL
              AND s.space_headway > 0
              AND s.space_headway < headway_threshold
              AND s.lane_id IS NOT NULL

            WITH min_duration, stepSize,
                v.id AS vehicle,
                s.lane_id AS lane_id,
                s.following AS following_vehicle,
                s.space_headway AS space_headway,
                s.timestamp AS timestamps
            ORDER BY vehicle, timestamps
            WITH
                vehicle,min_duration, stepSize,
                collect(lane_id) AS lanes,
                collect(following_vehicle) AS following_vehicles,
                collect(space_headway) AS gaps,
                collect(timestamps) AS timestamps
            // Building P2 intervals by scanning the ordered timestamps and checking for consecutive states with the same lane and following vehicle.
            WITH vehicle, lanes,following_vehicles,gaps,timestamps, min_duration, stepSize,
                // Initialize the accumulator for the reduce function.
                reduce(
                acc = {
                  intervals: [],
                  start: timestamps[0],
                  prev: timestamps[0],
                  lane: lanes[0],
                  follower: following_vehicles[0],
                  intervalTimestamps: [timestamps[0]],
                  intervalSpaceHeadways: [gaps[0]],
                  countStates: 1
                },
                // Iterate over the timestamps starting from the second one.
                i IN range(1, size(timestamps) - 1) |
                CASE // Check if the current state is consecutive to the previous one and has the same lane and leading vehicle.
                  WHEN timestamps[i] = acc.prev + stepSize
                    AND lanes[i] = acc.lane
                    AND following_vehicles[i] = acc.follower
                  THEN { 
                    intervals: acc.intervals,
                    start: acc.start,
                    prev: timestamps[i],
                    lane: acc.lane,
                    follower: acc.follower,
                    intervalTimestamps: acc.intervalTimestamps + [timestamps[i]],
                    intervalSpaceHeadways: acc.intervalSpaceHeadways + [gaps[i]],
                    countStates: acc.countStates + 1
                  }
                  ELSE { // If not consecutive or different lane/leader, close the previous interval and start a new one.
                    intervals: acc.intervals + [{
                      start: acc.start,
                      end: acc.prev,
                      lane: acc.lane,
                      follower: acc.follower,
                      timestamps: acc.intervalTimestamps,
                      spaceHeadways: acc.intervalSpaceHeadways,
                      numberOfStates: acc.countStates
                    }], // Close the previous interval.
                    start: timestamps[i],
                    prev: timestamps[i],
                    lane: lanes[i],
                    follower: following_vehicles[i],
                    intervalTimestamps: [timestamps[i]],
                    intervalSpaceHeadways: [gaps[i]],
                    countStates: 1
                  }
                END
              ) AS result
            // Append the final open interval after processing all timestamps.
            WITH
              vehicle,
              result.intervals + [{
                start: result.start,
                end: result.prev,
                lane: result.lane,
                follower: result.follower,
                timestamps: result.intervalTimestamps,
                spaceHeadways: result.intervalSpaceHeadways,
                numberOfStates: result.countStates
              }] AS gapIntervals,
              min_duration,
              stepSize

            UNWIND gapIntervals AS gapInterval

            RETURN
              vehicle AS vehicle_id, 
              gapInterval.follower AS following_vehicle_id,
              gapInterval.start AS P2_start,
              gapInterval.end AS P2_end,
              gapInterval.lane AS lane,
              //gapInterval.timestamps AS timestamps, 
              //gapInterval.spaceHeadways AS space_headways, 
              gapInterval.numberOfStates AS number_of_states
        }
        RETURN DISTINCT
            'http://example.org/traffic#vehicle_' + toString(vehicle_id) AS tp1_x, 'http://example.org/traffic#vehicle_' + toString(following_vehicle_id) AS tp1_y, P2_start AS tp1_p2Start, P2_end AS tp1_p2End
    }

    WITH tp1_x, tp1_y, tp1_p2Start, tp1_p2End

    RETURN collect(
        DISTINCT {tp1_x: tp1_x, tp1_y: tp1_y, tp1_p2Start: tp1_p2Start, tp1_p2End: tp1_p2End}
    ) AS tp1_rows
}

UNWIND tp0_rows AS tp0_row

WITH *, tp0_row.tp0_x AS tp0_x, tp0_row.tp0_y AS tp0_y, tp0_row.tp0_p1Start AS tp0_p1Start, tp0_row.tp0_p1End AS tp0_p1End

UNWIND [tp1_row IN tp1_rows WHERE tp1_row.tp1_x = tp0_x AND tp1_row.tp1_y = tp0_y] AS tp1_row

WITH *, tp1_row.tp1_x AS tp1_x, tp1_row.tp1_y AS tp1_y, tp1_row.tp1_p2Start AS tp1_p2Start, tp1_row.tp1_p2End AS tp1_p2End

RETURN 
    tp0_x AS x,
    tp0_y AS y,
    tp0_p1Start AS p1Start,
    tp0_p1End AS p1End,
    tp1_p2Start AS p2Start,
    tp1_p2End AS p2End