const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});
    const lib = b.addStaticLibrary(.{
        .name = "atak",
        .root_source_file = .{ .cwd_relative = "src/atak.zig" },
        .target = target,
        .optimize = optimize,
    });
    _ = b.addModule("atak", .{
        .root_source_file = .{ .cwd_relative = "src/atak.zig" },
        .target = target,
        .optimize = optimize,
    });

    const test_step = b.step("test", "Run library tests");
    const lib_tests = b.addTest(.{
        .root_source_file = .{ .cwd_relative = "src/atak.zig" },
        .target = target,
        .optimize = optimize,
    });
    test_step.dependOn(&b.addRunArtifact(lib_tests).step);

    b.installArtifact(lib);
}
