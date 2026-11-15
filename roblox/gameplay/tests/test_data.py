"""data_integrity: referential validity of all gameplay data tables."""
import sys

from harness import new_runtime, lua_list


def main():
    lua = new_runtime()
    errs = lua.eval("""(function()
        local D = {}
        for _, n in ipairs({"Items","Recipes","Machines","Research","Quests","Locations","Config"}) do
            D[n] = loadModule("shared/" .. n)
        end
        DATA = D
        return loadModule("shared/Validator").run(D)
    end)()""")
    errs = lua_list(errs)
    for e in errs:
        print("  FAIL", e)
    counts = lua.eval("""(function()
        local U = loadModule("shared/Util")
        local crafting, machines, logistics = 0, 0, 0
        for _, r in pairs(DATA.Recipes) do if not r.supply then crafting = crafting + 1 end end
        for _, m in pairs(DATA.Machines) do
            if m.kind == "machine" or m.kind == "pump" then machines = machines + 1 else logistics = logistics + 1 end
        end
        local steps = 0
        for _, c in pairs(DATA.Quests.chains) do steps = steps + #c.steps end
        return { U.count(DATA.Items), crafting, machines, logistics, U.count(DATA.Research), #DATA.Quests.mainOrder,
                 #DATA.Quests.orders, U.count(DATA.Quests.chains), steps, U.count(DATA.Locations.locations),
                 U.count(DATA.Locations.nodes) }
    end)()""")
    c = lua_list(counts)
    print(f"  items {c[0]}, crafting recipes {c[1]}, machines {c[2]}, logistics/storage parts {c[3]}, research nodes {c[4]}")
    print(f"  main quests {c[5]}, order templates {c[6]}, npc chains {c[7]} ({c[8]} steps), locations {c[9]}, nodes {c[10]}")
    assert c[1] >= 30 and c[2] >= 15 and c[3] >= 10 and c[5] >= 20 and c[6] >= 20 and c[7] >= 8
    if errs:
        print(f"data_integrity: {len(errs)} errors")
        sys.exit(1)
    print("data_integrity: OK")


if __name__ == "__main__":
    main()
