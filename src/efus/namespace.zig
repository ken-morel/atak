const Namespace = struct {
    parent: ?*Namespace, // Optional parent namespace (for scoping)
    symbols: std.StringHashMap(Value),
    allocator: Allocator,

    pub fn init(allocator: Allocator, parent: ?*Namespace) Namespace {
        return .{
            .parent = parent,
            .symbols = std.StringHashMap(Value).init(allocator),
            .allocator = allocator,
        };
    }

    pub fn define(self: *Namespace, name: []const u8, value: Value) !void {
        try self.symbols.put(name, value);
    }

    pub fn lookup(self: *Namespace, name: []const u8) ?Value {
        if (self.symbols.get(name)) |val| return val;
        if (self.parent) |parent| return parent.lookup(name);
        return null;
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;

const objects = @import("objects.zig");
const Value = objects.Value;
