const Value = union(enum) {
    String: []const u8,
    Integer: i64,
    Float: f64,
    Boolean: bool,
};

const Efus = struct {
    instructions: []const Instruction,
    namespace: Namespace,
    allocator: Allocator,

    // Run all instructions in the namespace
    pub fn run(self: *Efus) !void {
        for (self.instructions) |inst| {
            try self.evaluateInstruction(inst);
        }
    }

    // Evaluate a single instruction
    fn evaluateInstruction(self: *Efus, inst: Instruction) !void {
        switch (inst) {
            .Tagdef => |tag| {
                // Store `tag.value` in the namespace under `tag.name`
                try self.namespace.define(tag.name, tag.value);
            },
            .FlowControl => |flow| {
                // Handle conditionals/loops recursively
                if (flow.condition) |cond| {
                    const result = try self.evaluateExpression(cond);
                    if (result.isTruthy()) {
                        for (flow.body) |body_inst| {
                            try self.evaluateInstruction(body_inst);
                        }
                    }
                }
            },
            // ... handle other instruction types
        }
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;
