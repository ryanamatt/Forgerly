# Fruchterman-Reingold Algorithm

## Normal Fruchterman-Reingold Algorithm

```PseudoCode
area := W * L;                      { Canvas Width and Length }
G := (V, E);                        { Vertices and Edges }
k := sqrt(area / abs(V));           { Optimal distance between nodes }

for i := 1 to iterations do begin
    { 1. Calculate Repulsive Forces }
    for v in V do begin
        v.disp := 0;                { Reset displacement vector }
        for u in V do begin
            if (u != v) then begin
                D := v.pos - u.pos; { Distance vector }
                v.disp := v.disp + (D / |D|) * fr(|D|);
            end
        end
    end

    { 2. Calculate Attractive Forces }
    for e in E do begin
        D := e.v.pos - e.u.pos;
        e.v.disp := e.v.disp - (D / |D|) * fa(|D|);
        e.u.disp := e.u.disp + (D / |D|) * fa(|D|);
    end

    { 3. Limit Movement (Temperature) }
    for v in V do begin
        v.pos := v.pos + (v.disp / |v.disp|) * min(|v.disp|, t);
        v.pos.x := max(-W/2, min(W/2, v.pos.x));
        v.pos.y := max(-L/2, min(L/2, v.pos.y));
    end

    { 4. Cooling Schedule }
    t := cool(t);           { Reduce "heat" to settle the graph }
end
```

## Narrative Forge Modified Fruchterman-Reingold Algorithm

```PseudoCode
{ --- Initialization --- }
area := W * H;
k := C_ATTRACTION * sqrt(area / size(input_nodes)); { Optimal distance }
t := initial_temperature;

for i := 1 to max_iterations do begin

    { 1. Calculate Repulsive Forces }
    for each u in input_nodes do begin
        u.displacement := (0, 0);
        for each v in input_nodes do begin
            if (u.id != v.id) then begin
                dist := distance(u.pos, v.pos);
                force := (k * k) / dist; { force_rep function }
                
                if (not u.is_fixed) then
                    u.displacement += (direction_vector * force * C_REPEL);
            end
        end
    end

    { 2. Calculate Attractive Forces }
    for each edge in input_edges do begin
        u := get_node(edge.node_a_id);
        v := get_node(edge.node_b_id);
        dist := distance(u.pos, v.pos);
        
        { Apply Narrative Scaling: Intensity modifies the pull }
        force := ((dist * dist) / k) * (edge.intensity / 10.0);
        
        if (not u.is_fixed) then
            u.displacement -= (direction_vector * force * C_ATTRACTION);
        if (not v.is_fixed) then
            v.displacement += (direction_vector * force * C_ATTRACTION);
    end

    { 3. Apply Displacement & Cooling }
    for each node in input_nodes do begin
        if (not node.is_fixed) then begin
            mag := magnitude(node.displacement);
            if (mag > 0) then begin
                { Limit movement by current temperature }
                node.pos += (node.displacement / mag) * min(mag, t);
                
                { Clamp to Canvas Boundaries }
                node.pos.x := clamp(node.pos.x, -W/2, W/2);
                node.pos.y := clamp(node.pos.y, -H/2, H/2);
            end
        end
    end

    t := t * C_COOLING; { Gradually settle the graph }
end
```

*Last Updated: 2025-12-21*