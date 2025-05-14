pub const efus = @import("efus.zig");
export fn atak() void {
    print("Atak!", .{});
}
const std = @import("std");
const print = std.debug.print;
