param([int]$SandProcessId,[switch]$ResumeAfterHoney)
$ErrorActionPreference='Stop'
$productionRoot='C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'
$episodeRoot=Join-Path $productionRoot '02_EPISODES\EP002_Impossible_Blankets'
$blenderBinary='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
Set-Location -LiteralPath $productionRoot
if ($SandProcessId -gt 0) { Wait-Process -Id $SandProcessId -ErrorAction SilentlyContinue }
function Run-Stage([string]$inputVersion,[string]$script,[string]$outputVersion,[string]$log,[string]$material='') {
    $inputFile=Join-Path $episodeRoot ('blend\EP002_v'+$inputVersion+'.blend')
    if (!(Test-Path -LiteralPath $inputFile)) { throw ('Missing input: '+$inputFile) }
    Write-Output ('BEGIN_STAGE '+$script+' '+$material)
    if ($material) { & $blenderBinary -b $inputFile --python (Join-Path $productionRoot ('tools\'+$script)) -- $material *> (Join-Path $episodeRoot ('edit\'+$log)) }
    else { & $blenderBinary -b $inputFile --python (Join-Path $productionRoot ('tools\'+$script)) *> (Join-Path $episodeRoot ('edit\'+$log)) }
    if ($outputVersion -and !(Test-Path -LiteralPath (Join-Path $episodeRoot ('blend\EP002_v'+$outputVersion+'.blend')))) { throw ('Stage failed: '+$script+'; see '+$log) }
    Write-Output ('COMPLETE_STAGE '+$script+' '+$material)
}
if (!$ResumeAfterHoney) {
    Run-Stage '012' 'ep002_refine_slime.py' '012b' 'slime_refine.log'
    Run-Stage '012b' 'ep002_bake_physical_liquid.py' '013' 'physical_honey.log' 'HONEY'
}
Run-Stage '013' 'ep002_bake_physical_liquid.py' '014' 'physical_water.log' 'WATER'
Run-Stage '014' 'ep002_bake_physical_liquid.py' '015' 'physical_lava.log' 'LAVA'
Run-Stage '015' 'ep002_simulate_sand.py' '015b' 'final_granular.log' '015b'
Run-Stage '015b' 'ep002_refine_glass.py' '015c' 'final_glass.log'
Run-Stage '015c' 'ep002_finish_materials.py' '016' 'finish_materials.log'
Run-Stage '016' 'ep002_4k_review.py' '' '4k_review.log'
Write-Output 'PHYSICS_AND_4K_REVIEW_COMPLETE'
